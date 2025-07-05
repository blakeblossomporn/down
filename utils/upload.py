import requests
import os

class VKVideoUploader:
    API_URL = "https://api.vk.com/method/"
    API_VERSION = "5.131"

    def __init__(self, access_token, group_id):
        self.access_token = access_token,
        self.group_id = group_id

    def find_video_file(self, release_name, threshold=5):
        release_keywords = release_name.lower().split('.')
        best_match = None
        best_score = 0

        for root, _, files in os.walk(self.output_dir):
            for file in files:
                file_lower = file.lower()
                if not file_lower.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    continue

                # Count keyword matches
                score = sum(1 for kw in release_keywords if kw in file_lower)

                if score > best_score:
                    best_score = score
                    best_match = os.path.join(root, file)

        if best_score >= threshold:
            return best_match
        return None

    def get_upload_url(self, title, description, group_id=None):
        params = {
            "access_token": self.access_token,
            "v": self.API_VERSION,
            "name": title,
            "description": description,
        }

        if group_id:
            params["group_id"] = group_id

        response = requests.get(f"{self.API_URL}video.save", params=params)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return None

        return data["response"]["upload_url"]

    def upload_video(self, title, description=""):
        file_path = self.find_video_file(title)
        if not file_path:
            return False

        print("Getting VK upload URL...")
        upload_url = self.get_upload_url(title, description, self.group_id)
        if not upload_url:
            return False

        file_size = os.path.getsize(file_path)
        print(f"Uploading video ({round(file_size / (1024*1024), 2)} MB)...")

        with open(file_path, 'rb') as video_file:
            response = requests.post(
                upload_url,
                files={"video_file": (os.path.basename(file_path), video_file)},
                stream=True
            )
            response.raise_for_status()

            result = response.json()
            if "error" in result:
                return False

        try:
            os.remove(file_path)

            parent_folder = os.path.dirname(file_path)
            if parent_folder != self.output_dir and not os.listdir(parent_folder):
                os.rmdir(parent_folder)

        except Exception as e:
            print(f"Failed to delete video or folder: {e}")

        return True

