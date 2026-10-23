#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影视仓 / TVBox 配置自动更新脚本
=================================
功能：
  1. 读取 config/sources.json 中的配置源列表
  2. 对每个源依次尝试"主线 + 备用"多个地址，自动做中文域名 punycode 转换；
     成功后把可用地址调到首位、本次失败的备用地址移到末尾，并写回 config/sources.json
  3. 校验返回内容是否为合法的 TVBox/影视仓 单仓配置（包含 sites/spiders/lives 等字段）
     或 多仓订阅（顶层含 urls 数组）
  4. 将每个源的最新配置保存到 output/<id>.json
  5. 生成多仓订阅文件 output/多仓订阅.json（可直接填进影视仓的"订阅"或"多仓"）
  6. 生成 shields 徽章 output/shield.json，并把各源状态写回 README
兼容：本脚本同时兼容 GitHub Actions 自动运行 与 本地手动运行。
在 GitHub Actions 中，环境变量 GITHUB_REPOSITORY 会被自动注入（格式 owner/repo），
用于拼出多仓订阅里指向本仓库 raw 文件的完整 URL。
用法：
  python scripts/update.py
"""
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.parse

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT, "config", "sources.json")
OUTPUT_DIR = os.path.join(ROOT, "output")

DEFAULT_REPO = "ccttyylab/ys-sources"  # 本地运行时的默认仓库名，GitHub Actions 会用 GITHUB_REPOSITORY 自动覆盖

# 注意：部分接口的反爬会针对"完整 Chrome UA"下发挑战页，反而用简洁 UA 能正常返回 JSON
USER_AGENT = "Mozilla/5.0"

# 按顺序尝试的 UA 列表。不同站点对 UA 的判定差异很大：
#   - 多数源用简洁 UA 即可正常返回 JSON
#   - 个别源（如 菜妮丝）只对 TVBox 客户端的 okhttp UA 返回配置，浏览器 UA 会拿到 HTML
# 依次尝试，任一成功即返回。
USER_AGENTS = [
    USER_AGENT,
    "okhttp/3.12.0",
]

TIMEOUT = 15  # 单个地址超时（秒）
MAX_RETRIES = 2  # 单个地址最大尝试次数（仅对超时/连接类瞬态错误重试）
RETRY_BACKOFF = 2  # 重试基础等待秒数
URL_INTERVAL = 1.0  # 每个地址之间的小间隔秒数（降低被限流概率）
SOURCE_INTERVAL = 2  # 每个源之间的间隔秒数（降低被限流概率）

# 判定"像 TVBox 单仓配置"的顶层字段
TVBOX_KEYS = ("sites", "spiders", "lives", "store", "exts", "parses", "flags")
# 多仓订阅格式：顶层为 urls 数组
MULTI_KEYS = ("urls", "订阅")


def _strip_js_comments(text: str) -> str:
    """剔除 JSON 中内嵌的 // 行注释（部分接口会在字段后追加免责注释）。"""
    lines = text.split("\n")
    cleaned = [ln for ln in lines if not ln.lstrip().startswith("//")]
    return "\n".join(cleaned)


def parse_json_lenient(text: str):
    """宽容解析：去 BOM/空白、剔 // 注释后优先整体 json.loads；
    若接口返回了拼接的多段 JSON，取第一段有效对象。"""
    text = text.lstrip("\ufeff").strip()
    text = _strip_js_comments(text)
    try:
        # strict=False 允许字符串中出现未转义的控制字符（部分接口的 JSON 不规范）
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        # 兼容"返回了多个 JSON 拼接在一起"的接口
        decoder = json.JSONDecoder(strict=False)
        try:
            obj, _ = decoder.raw_decode(text)
            return obj
        except Exception:
            raise


def idn_encode(url: str) -> str:
    """将 URL 中的中文（国际化）域名转成 punycode，避免 DNS 解析失败。
    例如：http://www.饭太硬.com/tv -> http://www.xn--sss604efuw.com/tv
    """
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    try:
        encoded_host = host.encode("idna").decode("ascii")
    except Exception:
        encoded_host = host  # 已是 ascii 或转换失败，原样使用
    netloc = encoded_host
    if parsed.port:
        netloc = f"{encoded_host}:{parsed.port}"
    return urllib.parse.urlunsplit(
        (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
    )


def is_valid_tvbox_config(data) -> bool:
    """粗略校验：返回内容是否像 TVBox/影视仓 配置（单仓或多仓订阅）。"""
    if not isinstance(data, dict):
        return False
    if any(key in data for key in TVBOX_KEYS):
        return True
    # 多仓订阅格式：{"urls": [{"name":..., "url":...}, ...]}
    if "urls" in data and isinstance(data.get("urls"), list) and data["urls"]:
        return True
    return False


def _should_retry(err: Exception, resp_text_len: int = -1) -> bool:
    """判断失败是否值得重试：
    - 超时/连接类瞬态错误：重试
    - 空响应 / JSON 解析失败（疑似服务端反爬冷却）：重试（加长等待）
    - 4xx/5xx、返回了内容但结构不对（确定性失败）：不重试
    """
    if isinstance(err, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    if isinstance(err, requests.exceptions.HTTPError):
        return False  # 4xx/5xx 为确定性失败
    if isinstance(err, json.JSONDecodeError):
        return True  # 空响应或非 JSON，可能是反爬/冷却，给一次机会
    if resp_text_len <= 0:
        return True  # 没有拿到任何内容
    return False


def _fetch_once(target: str, user_agent: str) -> dict:
    """用指定 UA 抓取一次并校验，失败直接抛出异常。"""
    last_err = None
    resp = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                target,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "application/json,text/plain,*/*",
                },
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            resp.raise_for_status()
            data = parse_json_lenient(resp.text)
            if not is_valid_tvbox_config(data):
                raise ValueError(
                    "返回内容不是 TVBox 配置（缺少 sites/spiders/lives 或 urls 字段）"
                )
            return data
        except Exception as e:  # noqa: BLE001
            last_err = e
            text_len = len(getattr(resp, "text", "") or "") if resp is not None else -1
            if _should_retry(e, text_len) and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF * attempt * 2
                print(f"      (第 {attempt} 次失败：{e}，{wait}s 后重试)")
                time.sleep(wait)
            else:
                break
    raise last_err


def reorder_urls_on_success(urls: list, success_index: int) -> list:
    """成功地址置顶，本次尝试中失败的地址按原顺序移到末尾。"""
    if success_index <= 0 or success_index >= len(urls):
        return list(urls)
    winner = urls[success_index]
    failed = urls[:success_index]
    rest = urls[success_index + 1 :]
    return [winner] + rest + failed


def fetch_config(url: str) -> dict:
    """抓取单个地址并解析为 JSON dict；失败时抛出异常。

    依次尝试 USER_AGENTS 中的每个 UA：某些站点按 UA 分流，
    浏览器 UA 拿到 HTML、TVBox 客户端的 okhttp UA 才能拿到 JSON。
    """
    target = idn_encode(url)
    errors = []
    for idx, ua in enumerate(USER_AGENTS):
        try:
            return _fetch_once(target, ua)
        except Exception as e:  # noqa: BLE001
            errors.append(f"UA={ua}: {e}")
            # 换下一个 UA 再试（仅当还有备选时提示）
            if idx < len(USER_AGENTS) - 1:
                print(f"      (UA={ua} 失败，尝试下一个 UA)")
    # 全部 UA 都失败时，抛出汇总后的最后一个错误
    raise RuntimeError("；".join(errors))


README_PATH = os.path.join(ROOT, "README.md")
STATUS_START = "<!-- STATUS_START -->"
STATUS_END = "<!-- STATUS_END -->"


URL_WRAP_WIDTH = 44  # 表格内 URL 单行最大字符数，超出则在 "/" 处用 <br> 断行


def _break_url(url, width=URL_WRAP_WIDTH):
    """把超长 URL 在 "/" 处用 <br> 断行，避免把 Markdown 表格撑得过宽。

    只在分隔符后断行，断点本身仍属于 URL，便于阅读；单元格内仍是一整条链接。
    """
    url = str(url).replace("|", "/")
    if len(url) <= width:
        return url

    # 在 "/" 之后切分，保留 "https://" 这类协议的完整前缀
    tokens = re.findall(r"[^/]*/+|[^/]+$", url)
    lines, cur = [], ""
    for tk in tokens:
        if cur and len(cur) + len(tk) > width:
            lines.append(cur)
            cur = tk
        else:
            cur += tk
    if cur:
        lines.append(cur)
    return "<br>".join(lines)


def _short_err(err, limit=56):
    """把错误信息压缩成一行较短的可读文本，去除重复的 URL 噪声。"""
    text = str(err or "").replace("|", "/").replace("\n", " ").strip()
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def update_readme(status, ok_count, total):
    """把各源更新状态以表格形式写回 README（在 STATUS_START/END 标记之间）。"""
    if not os.path.exists(README_PATH):
        return
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()
    if STATUS_START not in readme or STATUS_END not in readme:
        return  # 未放置标记则不改动

    lines = []
    lines.append(
        f"> 🔄 最近更新：{status['updated_at']}（北京时间） · "
        f"成功 **{ok_count}/{total}** 个源"
    )
    lines.append("")
    lines.append("| 配置源 | 状态 | 使用地址 |")
    lines.append("| :--- | :---: | :--- |")
    for s in status["sources"]:
        if s.get("cached"):
            lines.append(f"| {s['name']} | 📦 缓存 | 沿用上次成功配置 |")
        elif s["ok"]:
            # 用 HTML <code> 而非反引号：Markdown 的 inline code 不会渲染 <br>，
            # 而 <code> 内的 <br> 可以正常换行，避免长 URL 把表格撑宽。
            lines.append(
                f"| {s['name']} | ✅ | "
                f"<code>{html.escape(_break_url(s['used_url']), quote=False).replace('&lt;br&gt;', '<br>')}</code> |"
            )
        else:
            lines.append(f"| {s['name']} | ❌ | {_short_err(s.get('error'))} |")
    block = "\n".join(lines)

    prefix = readme.split(STATUS_START, 1)[0]
    suffix = readme.split(STATUS_END, 1)[1]
    new_readme = f"{prefix}{STATUS_START}\n{block}\n{STATUS_END}{suffix}"
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_readme)


def write_badge(ok_count, total):
    """生成 shields.io endpoint 徽章 JSON。"""
    if total == 0 or ok_count == 0:
        color = "red"
    elif ok_count < total:
        color = "orange"
    else:
        color = "green"
    badge = {
        "schemaVersion": 1,
        "label": "TVBox 配置",
        "message": f"{ok_count}/{total} 可用",
        "color": color,
    }
    with open(os.path.join(OUTPUT_DIR, "shield.json"), "w", encoding="utf-8") as f:
        json.dump(badge, f, ensure_ascii=False, indent=2)


def main() -> int:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 东八区时间，便于阅读
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    # GitHub Actions 中自动注入 GITHUB_REPOSITORY=owner/repo
    repo = (
        os.environ.get("GITHUB_REPOSITORY")
        or os.environ.get("REPO")
        or DEFAULT_REPO
    )
    raw_base = f"https://gh-proxy.org/https://raw.githubusercontent.com/{repo}/main/output"

    status = {"updated_at": now_str, "repo": repo, "sources": []}
    subscriptions = []

    ok_count = 0
    config_urls_changed = False
    for src in cfg.get("sources", []):
        name = src.get("name", "未知")
        sid = src.get("id", name)
        urls = src.get("urls", [])

        entry = {"id": sid, "name": name, "ok": False, "used_url": None, "error": None}
        saved = False

        success_index = None
        for idx, url in enumerate(urls):
            try:
                data = fetch_config(url)
                out_path = os.path.join(OUTPUT_DIR, f"{sid}.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                entry["ok"] = True
                entry["used_url"] = url
                entry["error"] = None
                subscriptions.append(
                    {"name": name, "url": f"{raw_base}/{sid}.json"}
                )
                ok_count += 1
                saved = True
                success_index = idx
                print(f"[OK]   {name} <- {url}")
                break
            except Exception as e:  # noqa: BLE001
                print(f"[FAIL] {name}  {url}  ->  {e}")
                entry["error"] = str(e)

            # 地址之间稍作间隔，避免被限流
            time.sleep(URL_INTERVAL)

        if not saved:
            # 所有地址都失败：尝试使用上一次成功抓取的缓存文件
            cache_path = os.path.join(OUTPUT_DIR, f"{sid}.json")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    if is_valid_tvbox_config(cached):
                        subscriptions.append(
                            {"name": name, "url": f"{raw_base}/{sid}.json"}
                        )
                        entry["ok"] = True
                        entry["cached"] = True
                        entry["used_url"] = "(缓存)"
                        ok_count += 1
                        saved = True
                        print(f"[CACHE] {name}  使用上次缓存配置")
                except Exception:
                    pass
            if not saved:
                entry["error"] = entry["error"] or "所有地址均失败"
                print(f"[FAIL] {name}  全部地址失败")

        if success_index is not None:
            new_urls = reorder_urls_on_success(urls, success_index)
            if new_urls != urls:
                src["urls"] = new_urls
                config_urls_changed = True
                print(f"[REORDER] {name} 首选 -> {new_urls[0]}")

        status["sources"].append(entry)

        # 源之间稍作间隔，避免集中请求被限流
        time.sleep(SOURCE_INTERVAL)

    if config_urls_changed:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("已写回 config/sources.json（备用地址顺序已调整）")

    # 生成多仓订阅文件（影视仓"订阅/多仓"格式）
    sub_path = os.path.join(OUTPUT_DIR, "多仓订阅.json")
    with open(sub_path, "w", encoding="utf-8") as f:
        json.dump({"urls": subscriptions}, f, ensure_ascii=False, indent=2)

    # 生成更新状态文件（时间取全部抓取完成之后）
    status["updated_at"] = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(OUTPUT_DIR, "status.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    # 生成 shields 徽章并更新 README 状态表
    total = len(cfg.get("sources", []))
    write_badge(ok_count, total)
    update_readme(status, ok_count, total)

    print("\n" + "=" * 50)
    print(f"本次更新：{ok_count}/{total} 个源成功")
    print(f"多仓订阅：{sub_path}")
    if ok_count == 0:
        print("没有任何源更新成功，返回非 0 退出码。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
