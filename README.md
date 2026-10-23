# 影视仓配置聚合仓库（TVBox Config Aggregator）

![配置状态](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fccttyylab%2Fys-sources%2Fmain%2Foutput%2Fshield.json)
![更新频率](https://img.shields.io/badge/%E6%9B%B4%E6%96%B0-%E6%AF%8F%E5%A4%A9%202%20%E6%AC%A1-blue)

聚合 **肥猫、饭太硬、王二小、老刘备、小马、讴歌（欧歌）、4K小盒子、小盒子单仓、拾光多仓、挺好分享多仓、盒子迷、科技长青、香雅情、荐片平台、俊哥、摸鱼、菜妮丝** 等 17 个影视仓 / TVBox 单仓配置，通过 **GitHub Actions 定时自动更新**，并把结果直接提交回本仓库，供影视仓、TVBox、OK影视等软件随时拉取最新接口。

> 所有配置均来自互联网公开分享，版权归原作者所有；本仓库仅做聚合与镜像，仅供学习交流，请勿商用。

---

## 一、源可用性状态

<!-- STATUS_START -->
> 🔄 最近更新：2026-10-23 16:48:38（北京时间） · 成功 **17/17** 个源

| 配置源 | 状态 | 使用地址 |
| :--- | :---: | :--- |
| 🚀肥猫线路 | ✅ | <code>http://肥猫.net/tv</code> |
| 🚀饭太硬（镜像） | ✅ | <code>http://xhztv.top/dc/饭太硬/api.json</code> |
| 🚀王二小放牛娃 | ✅ | <code>https://d.kstore.dev/download/9280/wex.json</code> |
| 🚀老刘备 | ✅ | <code>https://raw.liucn.cc/box/m.json</code> |
| 🚀小马 | ✅ | <code>https://szyyds.cn/tv/x.json</code> |
| 🚀欧歌 | 📦 缓存 | 沿用上次成功配置 |
| 🚀小盒子4K | ✅ | <code>http://xhztv.top/4k.json</code> |
| 🚀小盒子 | ✅ | <code>http://xhztv.top/xhz</code> |
| 🚀拾光多仓 | ✅ | <code>http://xmbjm.fh4u.org/dc.txt</code> |
| 🚀挺好分享多仓 | ✅ | <code>http://ztha.top/TVBox/GYCK.json</code> |
| 🚀盒子迷 | ✅ | <code>https://盒子迷.top/禁止贩卖</code> |
| 🚀科技长青 | ✅ | <code>https://13413.kstore.vip/tv/changqing.json</code> |
| 🚀香雅情线路 | ✅ | <code>https://ghfast.top/https://<br>raw.githubusercontent.com/xyq254245/<br>xyqonlinerule/main/XYQTVBox.json</code> |
| 🚀荐片平台 | ✅ | <code>https://tv.203511.xyz/0821.json</code> |
| 🚀俊哥 | ✅ | <code>http://home.jundie.top:81/top98.json</code> |
| 🚀摸鱼儿 | ✅ | <code>https://6800.kstore.vip/fish.json</code> |
| 🚀菜妮丝 | ✅ | <code>https://tv.菜妮丝.top</code> |
<!-- STATUS_END -->

## 二、仓库结构

```
ys-sources/
├── .github/workflows/update.yml   # GitHub Actions 自动更新工作流
├── config/sources.json            # 配置源列表（主地址 + 备用地址），可自行增删改
├── scripts/update.py              # 核心更新脚本（下载→校验→合并→落盘→更新状态）
├── output/                        # 更新产物（由脚本自动生成并提交）
│   ├── 多仓订阅.json               # 多仓聚合订阅（推荐，App 内可切换各源）
│   ├── shield.json                # shields.io 状态徽章数据
│   ├── status.json                # 各源更新状态（机器可读）
│   ├── feimao.json / fantaiying.json / ...  # 各源独立配置
│   └── ...
├── requirements.txt
└── README.md
```

## 三、在影视仓 / TVBox 中使用

把下面的地址填入 App 的「设置 → 配置地址」即可。

### 3.1 多仓订阅（推荐）

一个地址搞定，App 内可自由切换各源，每个源跑在各自的 `spider` 上，互不干扰：

```
https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/多仓订阅.json
```

### 3.2 单源订阅

地址由「公共前缀 + 文件名」拼成，按需取用。

**公共前缀**

```
https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/
```

**文件名对照表**

| 源 | 文件名 | 说明 |
| :--- | :--- | :--- |
| 🚀肥猫线路 | [`feimao.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/feimao.json) | |
| 🚀饭太硬（镜像） | [`fantaiying.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/fantaiying.json) | |
| 🚀王二小放牛娃 | [`wangerxiao.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/wangerxiao.json) | |
| 🚀老刘备 | [`laoliubei.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/laoliubei.json) | |
| 🚀小马 | [`xiaoma.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/xiaoma.json) | |
| 🚀欧歌 | [`ouge.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/ouge.json) | 源站已加验证，靠缓存更新 |
| 🚀小盒子4K | [`4k.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/4k.json) | |
| 🚀小盒子 | [`xiaohezi.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/xiaohezi.json) | |
| 🚀拾光多仓 | [`shiguang.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/shiguang.json) | |
| 🚀挺好分享多仓 | [`tinghao.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/tinghao.json) | |
| 🚀盒子迷 | [`hezimii.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/hezimii.json) | |
| 🚀科技长青 | [`kejichangqing.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/kejichangqing.json) | |
| 🚀香雅情线路 | [`xiangyaqing.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/xiangyaqing.json) | |
| 🚀荐片平台 | [`jianpian.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/jianpian.json) | |
| 🚀俊哥 | [`junge.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/junge.json) | |
| 🚀摸鱼儿 | [`moyu.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/moyu.json) | |
| 🚀菜妮丝 | [`cainisi.json`](https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/cainisi.json) | 需 okhttp UA，脚本已自动回退 |

> 表内文件名可点击直达，方便直接复制 raw 内容。
> 多仓订阅与单仓文件里的地址由脚本根据 `GITHUB_REPOSITORY` 环境变量自动生成。

### 3.3 访问加速

国内直连 `raw.githubusercontent.com` 可能较慢，可在地址前套一层加速前缀，例如：

```
https://gh-proxy.org/https://raw.githubusercontent.com/ccttyylab/ys-sources/main/output/多仓订阅.json
```

## 四、自动更新机制

- 推送后，GitHub 自动识别 `.github/workflows/update.yml`。
- 默认每天 **02:00 和 14:00（UTC，即北京时间 10:00 和 22:00）** 自动更新一次。
- 也可在 **Actions → Auto Update TVBox Configs → Run workflow** 手动触发。
- 更新结果自动提交回 `main` 分支，README 状态表与徽章同步刷新。
- 工作流使用内置 `GITHUB_TOKEN`，无需配置任何密钥。

## 五、自定义配置源

编辑 `config/sources.json` 即可增删配置源或更换地址：

```json
{
  "id": "mysource",
  "name": "我的源",
  "urls": [
    "https://example.com/tv",
    "https://backup.example.com/tv"
  ]
}
```

- `id`：输出文件名（建议英文小写）。
- `name`：在多仓订阅与状态表中展示的名字。
- `urls`：依次尝试的地址列表，第一个成功的会被使用；可按“主地址在前、备用在后”排列。
- 修改后推送到 `main` 分支即会自动触发一次更新。
- 若某个源持续失败但曾有成功记录，脚本会自动沿用 `output/` 中的旧文件（状态表标记为 📦 缓存）。

## 六、本地手动更新（可选）

```bash
pip install -r requirements.txt
REPO=ccttyylab/ys-sources python scripts/update.py
```

## 七、脚本特性

- **中文域名自动转 punycode**：`饭太硬.com` → `xn--sss604efuw.com`，避免 DNS 解析失败。
- **多地址回退**：每个源按顺序尝试主/备用地址，单个地址失败不影响其他源。
- **智能重试**：仅对超时、连接错误、空响应等瞬态问题退避重试；4xx/5xx 等确定性失败直接跳过。
- **兼容多仓订阅**：既支持单仓（含 sites 字段），也支持多仓订阅（顶层 urls 数组）格式。
- **反爬兼容**：使用简洁 UA（部分接口对完整浏览器 UA 下发挑战页），自动剔除 JSON 内嵌的 `//` 注释，兼容未转义控制字符。
- **不提供聚合单仓**：不同源的站点绑定在各自的 `spider` jar 上（类名空间互不兼容），强行合并会导致大量站点无法播放，因此只产出多仓订阅与各源独立配置。
- **状态可视化**：每次更新自动刷新 README 状态表与 shields.io 徽章。
- **部分成功可用**：只要有一个源成功就产出可用订阅，失败源记录在 `status.json` 与 README 状态表。

## 八、常见问题

- **某个源一直失败？** 大部分源做了地区/频率限制，GitHub Actions 与本地网络环境不同，可能某个环境能访问、另一个不能。脚本会按 `urls` 顺序自动尝试所有备用地址，只把成功的写入。
- **自动提交会不会死循环？** 不会。push 触发只监听 `config/`、`scripts/`、`requirements.txt` 的变更，自动提交只改 `output/` 与 README 状态区，不会再次触发。

## 九、免责声明

本项目仅用于学习、测试与个人使用；聚合的接口资源来自互联网公开分享，版权归原作者所有。若涉及侵权，请联系删除相应内容。
