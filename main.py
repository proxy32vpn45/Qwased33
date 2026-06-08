import asyncio
import aiohttp
import base64
import urllib.parse
import random

# =====================================================
# ⚙️ НАСТРОЙКИ
# =====================================================

SOURCE_SUBS = [
    "https://raw.githubusercontent.com/Temnuk/naabuzil/refs/heads/main/1week",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt",
    "https://gitverse.ru/api/repos/flaafix/AetrisVPN/raw/branch/master/AetrisVPN.txt",
    "https://raw.githubusercontent.com/VansFenix/WildVF-/refs/heads/main/VansFenix%231",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-all.txt",
    
    
]

OUTPUT_FILE = "output.txt"

TIMEOUT = 1.5
MAX_TASKS = 300

REMOVE_DUPLICATES = True
SHUFFLE = False

# =====================================================
# 🌐 SUPPORTED ПРОТОКОЛЫ
# =====================================================

SUPPORTED = [
    "vless://",
    "vmess://",
    "trojan://",
    "ss://",
    "ssr://",
    "hysteria://",
    "hysteria2://",
    "tuic://",
    "reality://",
]

# =====================================================
# 📥 ЗАГРУЗКА
# =====================================================

async def fetch(session, url):
    try:
        async with session.get(url, timeout=20) as r:
            return await r.text()
    except:
        return ""


def decode(text):
    try:
        decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
        if any(p in decoded for p in SUPPORTED):
            return decoded
    except:
        pass
    return text


def extract(text):
    return [
        line.strip()
        for line in text.splitlines()
        if any(line.startswith(p) for p in SUPPORTED)
    ]


async def load_sources(session):
    all_nodes = []

    for url in SOURCE_SUBS:
        raw = await fetch(session, url)
        if not raw:
            continue

        raw = decode(raw)
        all_nodes.extend(extract(raw))

    return all_nodes

# =====================================================
# ⚡ ЛЁГКАЯ ПРОВЕРКА (УЛУЧШЕННАЯ)
# =====================================================

def detect_type(cfg):
    for p in SUPPORTED:
        if cfg.startswith(p):
            return p
    return "unknown"


async def tcp_check(host, port):
    try:
        loop = asyncio.get_running_loop()
        start = loop.time()

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=TIMEOUT
        )

        latency = int((loop.time() - start) * 1000)

        writer.close()
        await writer.wait_closed()

        return latency

    except:
        return None


async def check_node(cfg):
    try:
        if "@" not in cfg:
            return None

        proto = detect_type(cfg)

        host = cfg.split("@")[1].split(":")[0]
        port = int(cfg.split("@")[1].split("#")[0])

        # =================================================
        # 🔥 ОСНОВНАЯ ПРОВЕРКА
        # =================================================
        if proto in ["vless://", "vmess://", "trojan://", "ss://"]:
            latency = await tcp_check(host, port)
            if latency is None:
                return None
            return cfg, latency

        # =================================================
        # 🌐 ЛЁГКАЯ ПРОВЕРКА ДЛЯ СЛОЖНЫХ
        # =================================================
        elif proto in ["hysteria://", "hysteria2://", "tuic://", "reality://"]:
            latency = await tcp_check(host, port)
            if latency is None:
                return None

            # добавляем небольшой штраф (чтобы было честнее)
            latency += 250

            return cfg, latency

        else:
            return None

    except:
        return None


async def check_all(nodes):
    sem = asyncio.Semaphore(MAX_TASKS)

    async def worker(n):
        async with sem:
            return await check_node(n)

    tasks = [worker(n) for n in nodes]
    res = await asyncio.gather(*tasks)

    return [r for r in res if r]

# =====================================================
# 📊 СОРТИРОВКА
# =====================================================

def sort_nodes(nodes):
    return sorted(nodes, key=lambda x: x[1])

# =====================================================
# 🏷 ВЫВОД (НЕ МЕНЯЕМ КОНФИГ)
# =====================================================

def format_node(cfg, index):
    return f"#{index} | {cfg}"

# =====================================================
# 🚀 MAIN
# =====================================================

async def main():
    async with aiohttp.ClientSession() as session:

        print("📥 Loading...")
        nodes = await load_sources(session)

        print("🔎 Found:", len(nodes))

        if REMOVE_DUPLICATES:
            nodes = list(dict.fromkeys(nodes))

        print("⚡ Checking...")
        checked = await check_all(nodes)

        print("✅ Alive:", len(checked))

        checked = sort_nodes(checked)

        final = []
        for i, (cfg, lat) in enumerate(checked, start=1):
            final.append(format_node(cfg, i))

        if SHUFFLE:
            random.shuffle(final)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final))

        print("📦 Saved →", OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())
