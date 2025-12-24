import asyncio
import logging
import sys
import os

# Ensure import paths work
sys.path.append(os.getcwd())

from app.services.background import check_all_mods

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

async def main():
    print("Starting manual check...")
    await check_all_mods()
    print("Finished manual check.")

if __name__ == "__main__":
    asyncio.run(main())
