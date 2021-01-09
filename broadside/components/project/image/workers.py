import os
from pathlib import Path

from ...worker import Worker
from ....models.image import normalize


class ReadImagesWorker(Worker):
    def task(self, path: Path) -> None:
        filepaths = []
        for root, dirs, files in os.walk(path):
            root = Path(root)
            for file in files:
                filepaths.append(root / file)

        images = []
        for path in filepaths:
            if self._stopped:
                break

            image = normalize(path)
            if image is not None:
                images.append(image)

        self.data.emit({"images": images})
