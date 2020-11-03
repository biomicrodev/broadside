#!/usr/bin/env conda run -n broadside python

import os
import sys
from hashlib import sha1
from pathlib import Path
from urllib.request import urlretrieve

from tqdm import tqdm

LOCI_TOOLS_VER = "6.3.1"
LOCI_TOOLS_URL = f"https://downloads.openmicroscopy.org/bio-formats/{LOCI_TOOLS_VER}/artifacts/loci_tools.jar"
LOCI_TOOLS_SHA1 = "bdf1a37b561fea02fd8d1c747bd34db3fc49667b"


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None) -> None:
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download(url: str, output_path: str) -> None:
    with DownloadProgressBar(
        unit="B", unit_scale=True, miniters=1, desc=url.split("/")[-1], file=sys.stdout
    ) as progress_bar:
        urlretrieve(url, filename=output_path, reporthook=progress_bar.update_to)


# Check if up to date
print("Checking for latest bioformats...")

root = Path(__file__).parent.parent.resolve()
jar_dir = root / "jars"
jar_dir.mkdir(exist_ok=True)

jar_path = jar_dir / "loci_tools.jar"

try:
    with open(jar_path, "rb") as file:
        existing_sha1 = sha1(file.read()).hexdigest()
    if existing_sha1 == LOCI_TOOLS_SHA1:
        print("\tup to date!")
        sys.exit(0)

except IOError:
    pass

# Downloading
print(f"\tdownloading bioformats from {LOCI_TOOLS_URL}")

download(LOCI_TOOLS_URL, jar_path)

with open(jar_path, "rb") as file:
    existing_sha1 = sha1(file.read()).hexdigest()
if existing_sha1 != LOCI_TOOLS_SHA1:
    os.remove(jar_path)
    raise RuntimeError("\tloci_tools.jar SHA1 hash mismatch")
