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
    "https://github.com/terik21/HiddifySubs-VlessKeys/raw/refs/heads/main/RU_other",
    "https://raw.githubusercontent.com/VansFenix/WildVF-/refs/heads/main/VansFenix%231",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-all.txt",
    "https://gist.githubusercontent.com/pidarasuebisov-afk/e220b44264242d1a97c0908aba091edd/raw/PKN%20cocnyL",
    "https://raw.githubusercontent.com/flaafix/AetrisVPN-white-list-lite/refs/heads/main/AetrisVPN.txt",
    "https://raw.githubusercontent.com/hiztin/VLESS-PO-GRIBI/main/deploy/subscriptions/1.txt"
]

OUTPUT_FILE = "output.txt"

TIMEOUT = 2
MAX_TASKS = 300

REMOVE_DUPLICATES = True
SHUFFLE = False

# =====================================================
# 🌐 SUPPORTED
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
# 📥 FETCH
# =====================================================

async def fetch(session, url):
    try:
        async with session.get(url, timeout=20) as r:
            return await r.text()
    except:
        return ""


# =====================================================
# 🔓 DECODE (НЕ ЛОМАЕТ ДАННЫЕ)
# =====================================================

def decode(text):
    try:
        return base64.b64decode(text).decode("utf-8", errors="ignore")
    except:
        return text


# =====================================================
# 🔎 EXTRACT (ИСПРАВЛЕНО)
# =====================================================

def extract(text):
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # мягкий фильтр — НЕ жёсткий startswith
        if any(p in line for p in SUPPORTED):
            lines.append(line)

    return lines


# =====================================================
# 📦 LOAD SOURCES
# =====================================================

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
# ⚡ TCP CHECK (МЯГКИЙ)
# =====================================================

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


# =====================================================
# 🧠 CHECK NODE (НЕ УБИВАЕТ ВСЁ)
# =====================================================

async def check_node(cfg):
    try:
        if "@" not in cfg:
            return None

        host = cfg.split("@")[1].split(":")[0]
        port_part = cfg.split(":")[-1]
        port = int("".join([c for c in port_part if c.isdigit()]))

        latency = await tcp_check(host, port)

        # 🔥 если проверка не удалась — НЕ выкидываем сразу
        if latency is None:
            latency = 9999  # плохой, но остаётся в списке

        return cfg, latency

    except:
        return None


# =====================================================
# 🔁 CHECK ALL
# =====================================================

async def check_all(nodes):
    sem = asyncio.Semaphore(MAX_TASKS)

    async def worker(n):
        async with sem:
            return await check_node(n)

    tasks = [worker(n) for n in nodes]
    res = await asyncio.gather(*tasks)

    return [r for r in res if r]


# =====================================================
# 📊 SORT
# =====================================================

def sort_nodes(nodes):
    return sorted(nodes, key=lambda x: x[1])


# =====================================================
# 🏷 OUTPUT
# =====================================================

def format_node(cfg):
    return cfg


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

        print("✅ Checked:", len(checked))

        # 🛡 fallback (чтобы output НЕ был пустой)
        if not checked:
            print("⚠️ No working nodes, saving raw list")
            checked = [(n, 9999) for n in nodes]

        checked = sort_nodes(checked)

        final = []
        for i, (cfg, lat) in enumerate(checked, start=1):
            final.append(cfg)

        if SHUFFLE:
            random.shuffle(final)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final))

        print("📦 Saved →", OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())
