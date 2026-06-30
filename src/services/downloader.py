import os
import tempfile
from typing import Callable
import yt_dlp


class Downloader:
    def download(self, url: str, on_progress: Callable[[float], None] | None = None) -> str:
        out_dir = tempfile.mkdtemp(prefix="videocutter_")
        out_template = os.path.join(out_dir, "%(title)s.%(ext)s")

        ydl_opts = {
            "outtmpl": out_template,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._make_hook(on_progress)] if on_progress else [],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            # yt-dlp may have merged to a different extension
            base = os.path.splitext(filename)[0]
            for ext in (".mp4", ".mkv", ".webm"):
                candidate = base + ext
                if os.path.exists(candidate):
                    return candidate
            raise FileNotFoundError(f"Downloaded file not found near: {filename}")

        return filename

    @staticmethod
    def _make_hook(callback: Callable[[float], None]):
        def hook(d: dict):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    callback(downloaded / total * 100)
        return hook
