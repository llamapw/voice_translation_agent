import shutil
from pathlib import Path
from typing import BinaryIO


class MediaService:
    def save_binary_file(self, source: BinaryIO, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            shutil.copyfileobj(source, output)
        return destination


media_service = MediaService()
