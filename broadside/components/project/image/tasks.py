# import os
# from pathlib import Path
# from typing import List
#
# from ...task import Task, Report
# from ....models.image import normalize, Image


# class ReadImagesTask(Task):
#     def run(self, path: Path, ext=(".svs", ".scn")) -> List[Image]:
#         filepaths = []
#         for root, dirs, files in os.walk(path):
#             root = Path(root)
#             for file in files:
#                 if file.endswith(ext):
#                     filepaths.append(root / file)
#
#         total = len(filepaths)
#
#         images = []
#         # with ProcessPoolExecutor(max_workers=5) as executor:
#         #     futures = {executor.submit(normalize, filepath) for filepath in filepaths}
#         #     for i, future in enumerate(as_completed(futures)):
#         #         self.progress.emit(Report(iter=i + 1, total=total))
#         #         image = future.result()
#         #         images.append(image)
#
#         for i, path in enumerate(filepaths):
#             if self._stopped:
#                 break
#
#             image = normalize(path)  # time-consuming
#             if image is not None:
#                 images.append(image)
#
#             self.progress.emit(Report(iter=i + 1, total=total))
#
#         return images
