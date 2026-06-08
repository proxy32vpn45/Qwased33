import asyncio
import aiohttp
import base64
import urllib.parse
import random

# =====================================================
# ⚙️ НАСТРОЙКИ (CONFIG)
# =====================================================

SOURCE_SUBS = [
    # 🔗 сюда вставляешь ссылки на подписки
]

OUTPUT_FILE = "output.txt"

TIMEOUT = 1.5  # ⏱ таймаут проверки (сек)
MAX_TASKS = 300  # ⚡ параллельные проверки

REMOVE_DUPLICATES = True  # 🧹 удалять дубликаты
SHUFFLE = False  # 🔀 перемешивать результат

SUPPORTED = ["vless://", "vmess://", "trojan://", "ss://"]

# =====================================================
# 🌍 ФЛАГИ СТРАН (много стран)
# =====================================================

FLAGS = {
    "RU": "🇷🇺", "US": "🇺🇸", "DE": "🇩🇪", "NL": "🇳🇱",
    "FR": "🇫🇷", "GB": "🇬🇧", "PL": "🇵🇱", "UA": "🇺🇦",
    "JP": "🇯🇵", "SG": "🇸🇬", "CA": "🇨🇦", "TR": "🇹🇷",
    "IT": "🇮🇹", "ES": "🇪🇸", "BR": "🇧🇷", "IN": "🇮🇳",
    "CN": "🇨🇳", "KR": "🇰🇷", "SE": "🇸🇪", "FI": "🇫🇮",
    "NO": "🇳🇴", "CH": "🇨🇭", "CZ": "🇨🇿", "RO": "🇷🇴",
    "BG": "🇧🇬", "HU": "🇭🇺", "AE": "🇦🇪", "SA": "🇸🇦",
}

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
        d = base64.b64decode(text).decode("utf-8", errors="ignore")
        if any(p in d for p in SUPPORTED):
            return d
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
# ⚡ ЛЁГКАЯ ПРОВЕРКА (TCP)
# =====================================================

async def check_node(cfg):
    try:
        if "@" not in cfg:
            return None

        host = cfg.split("@")[1].split(":")[0]
        port = int(cfg.split("@")[1].split("#")[0])

        loop = asyncio.get_running_loop()
        start = loop.time()

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=TIMEOUT
        )

        latency = int((loop.time() - start) * 1000)

        writer.close()
        await writer.wait_closed()

        return cfg, latency

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
# 📊 СОРТИРОВКА (лучшие сверху)
# =====================================================

def sort_nodes(nodes):
    return sorted(nodes, key=lambda x: x[1])

# =====================================================
# 🌍 ПРОСТОЕ ОПРЕДЕЛЕНИЕ СТРАНЫ
# =====================================================

def detect_country(cfg):
    cfg = cfg.lower()

    if "ru" in cfg:
        return "RU"
    if "us" in cfg:
        return "US"
    if "de" in cfg:
        return "DE"
    if "nl" in cfg:
        return "NL"
    if "fr" in cfg:
        return "FR"
    if "jp" in cfg:
        return "JP"
    if "pl" in cfg:
        return "PL"

    return "UN"

# =====================================================
# 🏷 ФОРМАТ ВЫВОДА
# =====================================================

def format_node(cfg, index):
    country = detect_country(cfg)
    flag = FLAGS.get(country, "🏳️")

    name = f"#{index} {flag} {country} | {cfg}"
    return name

# =====================================================
# 🚀 MAIN
# =====================================================

async def main():
    async with aiohttp.ClientSession() as session:

        print("📥 Загружаем подписки...")
        nodes = await load_sources(session)

        print("🔎 Найдено:", len(nodes))

        if REMOVE_DUPLICATES:
            nodes = list(dict.fromkeys(nodes))

        print("⚡ Проверяем...")
        checked = await check_all(nodes)

        print("✅ Живых:", len(checked))

        checked = sort_nodes(checked)

        final = []
        for i, (cfg, lat) in enumerate(checked, start=1):
            line = format_node(cfg, i)
            final.append(line)

        if SHUFFLE:
            random.shuffle(final)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final))

        print("📦 Готово →", OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())
