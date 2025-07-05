import requests
import os
import time
import subprocess
from dateutil import parser
from urllib.parse import quote_plus
from sqlalchemy.orm import Session
from .models import Torrent
from .upload import VKVideoUploader


class TorrentDownloader(VKVideoUploader):
    def __init__(self, milkie_token, milkie_api_key, vk_token, engine, vk_group_id=None, output_dir="torrents", new_release=False):
        super().__init__(vk_token, vk_group_id)

        self.base_url = "https://milkie.cc/api/v1/torrents"
        self.milkie_token = milkie_token
        self.milkie_api_key = quote_plus(milkie_api_key)
        self.session = Session(bind=engine)
        self.output_dir = output_dir
        self.new_release = new_release
        self.downloaded_ids = [u.torrent_id for u in self.session.query(Torrent.torrent_id).all()]
        self.headers = {
            "Authorization": f"Bearer {self.milkie_token}"
        }
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_page(self, page):
        params = {
            "oby": "created_at",
            "odir": "desc",
            "query": "",
            "categories": 7,
            "ad.q": "1080p",
            "pi": page,
            "ps": 100
        }
        response = requests.get(self.base_url, headers=self.headers, params=params)

        if response.status_code != 200:
            print(f"Error fetching page {page}: HTTP {response.status_code}")
            return []

        data = response.json()
        return data.get("torrents", [])

    def download_torrent_file(self, torrent):
        torrent_id = torrent["id"]
        release_name = torrent["releaseName"].replace("/", "_")
        filename = f"{release_name}.torrent"
        filepath = os.path.join(self.output_dir, filename)

        # if torrent_id in self.downloaded_ids:
        #     print(f"Skipped (already downloaded): {release_name}")
        #     return

        if torrent_id in self.downloaded_ids:
            if self.new_release:
                print(f"Found existing torrent in DB while in new_release mode: {release_name}. Stopping script.")
                exit(0)
            else:
                print(f"Skipped (already downloaded): {release_name}")
                return

        url = f"{self.base_url}/{torrent_id}/torrent"
        params = {"key": self.milkie_api_key}
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            return

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"Torrent: {release_name}")

        cmd = [
            "aria2c.exe",
            "--seed-time=0",
            "--dir", self.output_dir,
            "--summary-interval=0",
            "--console-log-level=error",
            filepath
        ]

        try:
            subprocess.run(cmd, check=True)
            os.remove(filepath)

            video_status = self.upload_video(title=release_name)
            if not video_status:
                return

            created_at_dt = parser.parse(torrent["createdAt"])
            new_torrent = Torrent(
                torrent_id=torrent["id"],
                release_name=torrent["releaseName"],
                created_at=created_at_dt,
                is_downloaded=True
            )
            self.session.add(new_torrent)
            self.session.commit()
            self.downloaded_ids.append(torrent["id"])

        except subprocess.CalledProcessError:
            print(f"❌ aria2c download failed for: {release_name}")
            print(f"⚠️ Keeping .torrent file: {filename}")

    def run(self):
        page = 0
        while True:
            torrents = self.fetch_page(page)
            if not torrents:
                print(f"\n✅ No more torrents on page {page}. Done.\n")
                break

            print(f"\n📄 Processing page {page} ({len(torrents)} items):\n")
            for torrent in torrents:
                self.download_torrent_file(torrent)
                time.sleep(1)  # avoid rate limiting

            page += 1

