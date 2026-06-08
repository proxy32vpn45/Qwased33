import asyncio
import aiohttp
from fetcher import load_all_sources
from config import REMOVE_DUPLICATES, OUTPUT_FILE


async def main():
    async with aiohttp.ClientSession() as session:

        print("Loading sources...")
        nodes = await load_all_sources(session)

        print(f"Found: {len(nodes)}")

        if REMOVE_DUPLICATES:
            nodes = list(dict.fromkeys(nodes))

        # пока без проверки (добавим во 2 части)
        final_nodes = nodes

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final_nodes))

        print(f"Saved: {len(final_nodes)}")


if __name__ == "__main__":
    asyncio.run(main())
