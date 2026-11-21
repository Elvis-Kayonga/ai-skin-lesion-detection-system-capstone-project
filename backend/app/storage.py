"""Where case photos and heatmaps are kept. `ImageStore` uses the disk (the database stores only the
paths); `DbImageStore` keeps the bytes in the database for hosts whose disk is wiped on restart."""
import io
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


class DbImageStore(ImageStore):
    """Keeps photos and heatmaps in the `stored_files` table. Paths look like "db:<name>"; older disk paths
    still work. Photos are reduced to at most 1024 px on the long side to keep the free database small."""

    PREFIX = "db:"
    MAX_SIDE = 1024

    def __init__(self, session_factory, root: Path):
        super().__init__(root)
        self._sessions = session_factory

    def save_case_files(self, image: Image.Image, heatmap_png: bytes) -> tuple[str, str]:
        from .models import StoredFile

        stem = uuid.uuid4().hex
        photo = image.copy()
        photo.thumbnail((self.MAX_SIDE, self.MAX_SIDE))
        buf = io.BytesIO()
        photo.convert("RGB").save(buf, format="JPEG", quality=85)
        image_key, heatmap_key = f"{stem}.jpg", f"{stem}_cam.png"
        with self._sessions() as db:
            db.add_all([StoredFile(key=image_key, data=buf.getvalue()), StoredFile(key=heatmap_key, data=heatmap_png)])
            db.commit()
        return self.PREFIX + image_key, self.PREFIX + heatmap_key

    def read(self, path: str | Path) -> bytes:
        path = str(path)
        if not path.startswith(self.PREFIX):
            return super().read(path)
        from .models import StoredFile

        with self._sessions() as db:
            row = db.get(StoredFile, path[len(self.PREFIX):])
            if row is None:
                raise FileNotFoundError(path)
            return row.data
