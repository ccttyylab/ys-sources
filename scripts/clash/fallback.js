/**
 * Clash JS Override Script - Final Stable Edition
 *
 * 特点：
 * 1. 保留全局 自动选择
 * 2. 地区仅保留：
 *    - XX-FALLBACK（显示）
 *    - XX-AUTO（隐藏）
 * 3. FALLBACK：
 *    优先节点顺序 -> 最后兜底 AUTO
 * 4. 所有软件默认 US-FALLBACK
 * 5. 漏网之鱼包含所有地区
 * 6. 不覆盖 DNS / Sniffer / GeoX
 */

const now = new Date();

const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(
  2,
  "0",
)}${String(now.getDate()).padStart(2, "0")}`;

const proxyName = `Clash 💤 ${dateStr}`;

const config = {
  testUrl: "https://cp.cloudflare.com/generate_204",

  testInterval: 300,

  excludeRegex: /(?:剩余|到期|主页|官网|游戏|关注|订阅|重置)/i,

  providers: {
    reject:
      "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt",

    direct:
      "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/direct.txt",

    proxy:
      "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/proxy.txt",

    google:
      "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/google.txt",

    cncidr:
      "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/cncidr.txt",

    lancidr:
      "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/lancidr.txt",

    openai:
      "https://fastly.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/OpenAI/OpenAI.yaml",

    claude:
      "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Claude/Claude.yaml",

    gemini:
      "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Gemini/Gemini.yaml",

    twitter:
      "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Twitter/Twitter.yaml",

    telegram:
      "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Telegram/Telegram.yaml",
  },

  regions: [
    {
      name: "HK/TW",

      regex:
        /香港|港|HK|Hong|Hong Kong|🇭🇰|台湾|台|TW|Taiwan|Wan|🇨🇳|🇹🇼|澳门|澳|MO|Macau|🇲🇴/i,
    },

    {
      name: "JP",

      regex: /日本|日|JP|Japan|Tokyo|Osaka|东京|大阪|🇯🇵/i,
    },

    {
      name: "KR",

      regex: /韩国|韩|KR|Korea|South Korea|Seoul|首尔|🇰🇷/i,
    },

    {
      name: "SG",

      regex: /新加坡|狮城|坡|SG|Singapore|🇸🇬/i,
    },

    {
      name: "US",

      regex:
        /美国|美区|美西|美东|美|US|USA|United States|America|Los Angeles|LA|San Jose|San Francisco|Seattle|Dallas|New York|NY|Ashburn|洛杉矶|圣何塞|旧金山|西雅图|达拉斯|纽约|🇺🇸/i,
    },
  ],
};

function main(params) {
  if (!params.proxies) params.proxies = [];

  overwriteRules(params);

  overwriteProxyGroups(params);

  return params;
}

function overwriteRules(params) {
  const providers = {};

  Object.keys(config.providers).forEach((key) => {
    const url = config.providers[key];

    providers[key] = {
      type: "http",

      behavior: url.includes(".yaml")
        ? "classical"
        : key.includes("cidr")
          ? "ipcidr"
          : "domain",

      url,

      path: `./ruleset/${key}.yaml`,

      interval: 86400,
    };
  });

  params["rule-providers"] = providers;

  params.rules = [
    "PROCESS-NAME,zerotier-one,DIRECT",
    "PROCESS-NAME,ZeroTier,DIRECT",
    "IP-CIDR,10.147.18.0/24,DIRECT,no-resolve",
    "DOMAIN-KEYWORD,qtrade,DIRECT",
    "DOMAIN-SUFFIX,cursor.com,Google",
    "DOMAIN-SUFFIX,cursor.sh,Google",

    "PROCESS-NAME,Telegram,Telegram",

    "RULE-SET,reject,广告拦截",

    "RULE-SET,openai,ChatGPT",

    "RULE-SET,claude,Claude",

    "RULE-SET,gemini,Gemini",

    "RULE-SET,google,Google",

    "RULE-SET,twitter,Twitter",

    "RULE-SET,telegram,Telegram",

    "RULE-SET,direct,DIRECT",

    "RULE-SET,lancidr,DIRECT",

    "RULE-SET,cncidr,DIRECT",

    "GEOIP,LAN,DIRECT,no-resolve",

    "GEOIP,CN,DIRECT,no-resolve",

    `RULE-SET,proxy,${proxyName}`,

    "MATCH,漏网之鱼",
  ];
}

function overwriteProxyGroups(params) {
  const allProxies = params.proxies.map((e) => e.name);

  const classified = {
    clean: [],

    dirty: [],

    regions: {},
  };

  config.regions.forEach((r) => {
    classified.regions[r.name] = [];
  });

  allProxies.forEach((name) => {
    if (config.excludeRegex.test(name)) {
      classified.dirty.push(name);

      return;
    }

    classified.clean.push(name);

    for (const region of config.regions) {
      if (region.regex.test(name)) {
        classified.regions[region.name].push(name);

        break;
      }
    }
  });

  const groups = [];

  const regionFallbackNames = [];

  config.regions.forEach((region) => {
    const nodes = classified.regions[region.name];

    if (!nodes.length) return;

    const autoName = `${region.name}-AUTO`;

    const fallbackName = `${region.name}-FALLBACK`;

    regionFallbackNames.push(fallbackName);

    // 隐藏 AUTO
    groups.push({
      name: autoName,

      type: "url-test",

      hidden: true,

      url: config.testUrl,

      interval: config.testInterval,

      tolerance: 100,

      "expected-status": "204",

      proxies: nodes,
    });

    // FALLBACK
    groups.push({
      name: fallbackName,

      type: "fallback",

      url: config.testUrl,

      interval: config.testInterval,

      tolerance: 100,

      "expected-status": "204",

      proxies: [...nodes, autoName],
    });
  });

  // 全局自动
  groups.unshift({
    name: "自动选择",

    type: "url-test",

    url: config.testUrl,

    interval: config.testInterval,

    tolerance: 100,

    "expected-status": "204",

    proxies: classified.clean.length ? classified.clean : ["DIRECT"],
  });

  // 全局手动
  groups.unshift({
    name: "手动选择",

    type: "select",

    proxies: classified.clean.length ? classified.clean : ["DIRECT"],
  });

  // 主代理
  groups.unshift({
    name: proxyName,

    type: "select",

    proxies: ["自动选择", ...regionFallbackNames, "手动选择", "DIRECT"],
  });

  // ChatGPT
  groups.push({
    name: "ChatGPT",

    type: "select",

    proxies: [
      "US-FALLBACK",

      "JP-FALLBACK",

      "SG-FALLBACK",

      "HK/TW-FALLBACK",

      "自动选择",

      "手动选择",

      "DIRECT",
    ],
  });

  // Claude
  groups.push({
    name: "Claude",

    type: "select",

    proxies: [
      "US-FALLBACK",

      "JP-FALLBACK",

      "SG-FALLBACK",

      "HK/TW-FALLBACK",

      "自动选择",

      "手动选择",

      "DIRECT",
    ],
  });

  // Gemini
  groups.push({
    name: "Gemini",

    type: "select",

    proxies: [
      "US-FALLBACK",

      "JP-FALLBACK",

      "SG-FALLBACK",

      "HK/TW-FALLBACK",

      "自动选择",

      "手动选择",

      "DIRECT",
    ],
  });

  // Google
  groups.push({
    name: "Google",

    type: "select",

    proxies: [
      "US-FALLBACK",

      "JP-FALLBACK",

      "SG-FALLBACK",

      "HK/TW-FALLBACK",

      "自动选择",

      "DIRECT",
    ],
  });

  // Twitter
  groups.push({
    name: "Twitter",

    type: "select",

    proxies: [
      "US-FALLBACK",

      "JP-FALLBACK",

      "SG-FALLBACK",

      "HK/TW-FALLBACK",

      "自动选择",

      "DIRECT",
    ],
  });

  // Telegram
  groups.push({
    name: "Telegram",

    type: "select",

    proxies: [
      "US-FALLBACK",

      "JP-FALLBACK",

      "SG-FALLBACK",

      "HK/TW-FALLBACK",

      "自动选择",

      "DIRECT",
    ],
  });

  // 漏网之鱼
  groups.push({
    name: "漏网之鱼",

    type: "select",

    proxies: [
      proxyName,

      "US-FALLBACK",

      "JP-FALLBACK",

      "SG-FALLBACK",

      "HK/TW-FALLBACK",

      "自动选择",

      "手动选择",

      "DIRECT",
    ],
  });

  // 广告拦截
  groups.push({
    name: "广告拦截",

    type: "select",

    proxies: ["REJECT", "DIRECT"],
  });

  // 脏节点
  if (classified.dirty.length > 0) {
    groups.push({
      name: "Other",

      type: "select",

      proxies: classified.dirty,
    });
  }

  params["proxy-groups"] = groups;
}
