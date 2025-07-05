import os
from dotenv import load_dotenv
from utils.db import engine
from utils.torrents import TorrentDownloader

load_dotenv()

if __name__ == "__main__":
    milkie_token = os.getenv("MILKIE_TOKEN")
    milkie_api_key = os.getenv("MILKIE_API_KEY")
    vk_token = os.getenv("VK_TOKEN")

    # Start Downloading
    downloader = TorrentDownloader(
        milkie_token=milkie_token,
        milkie_api_key=milkie_api_key,
        vk_token=vk_token,
        engine=engine,
        vk_group_id="230476631",
        output_dir="torrents",
        new_release=True,
    )
    downloader.run()
