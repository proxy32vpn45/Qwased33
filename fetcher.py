import base64
from config import SOURCE_SUBS, SUPPORTED


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


async def load_all_sources(session):
    all_nodes = []

    for url in SOURCE_SUBS:
        raw = await fetch(session, url)
        if not raw:
            continue

        raw = decode(raw)
        all_nodes.extend(extract(raw))

    return all_nodes
