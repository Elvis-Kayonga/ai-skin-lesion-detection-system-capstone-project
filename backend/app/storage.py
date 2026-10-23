"""Image files on disk. The database stores only the file paths."""
import uuid
from pathlib import Path

from PIL import Image


class ImageStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_case_files(self, image: Image.Image, heatmap_png: bytes) -> tuple[Path, Path]:
        """Save the (validated) photo and its heatmap under one random name; return both paths."""
        stem = uuid.uuid4().hex
        image_path = self.root / f"{stem}.jpg"
        heatmap_path = self.root / f"{stem}_cam.png"
        image.save(image_path, format="JPEG", quality=90)
        heatmap_path.write_bytes(heatmap_png)
        return image_path, heatmap_path

    def read(self, path: str | Path) -> bytes:
        return Path(path).read_bytes()
