import logging
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Set, Optional

import dask.array as da
import numpy as np
import zarr
from shapely.geometry import Polygon
from tifffile import TiffFile, TiffPageSeries, TiffPage
from tifffile.tifffile import ZarrTiffStore
from zarr import Group

from ..utils.serializable import Serializable
from ..utils.geom import PointF

NS_SCN = "{http://www.leica-microsystems.com/scn/2010/10/01}"


def str2int(s: str) -> int:
    return int(round(float(s)))


def is_dir_empty(path: Path) -> bool:
    if not path.is_dir():
        raise ValueError(f"Path not a directory!")
    return not any([True for _ in os.scandir(path)])


@dataclass
class ObjectGroup:
    name: str
    coords: np.ndarray
    polygons: List[Polygon]


@dataclass(frozen=True)
class Pyramid:
    """
    A Pyramid is a set of arrays that form a geometric sequence in image space.
    The microns per pixel value is the scale factor for the base array.
    The offset is in physical units.
    """

    layers: List[da.Array]
    mpp: PointF
    offset: PointF
    object_groups: List[ObjectGroup] = field(default_factory=list)


@dataclass(frozen=True)
class PyramidGroup:
    dtype: np.dtype
    channel_index: int
    n_channels: int
    axes: str
    file_format: str
    flags: Set[str]

    label: Optional[np.ndarray]
    pyramids: List[Pyramid]
    background: Optional[Pyramid] = None


@dataclass
class Annotation:
    name: str
    polygon: Polygon = None

    annotations_dir = "annotations"


@dataclass
class Color(Serializable):
    r: float
    g: float
    b: float
    a: float = 1.0

    def as_dict(self) -> Dict[str, Any]:
        return {"r": self.r, "g": self.g, "b": self.b, "a": self.a}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Color":
        r = dct.get("r", 1.0)
        g = dct.get("g", 1.0)
        b = dct.get("b", 1.0)
        a = dct.get("a", 1.0)
        return cls(r=r, g=g, b=b, a=a)


@dataclass
class Range(Serializable):
    min: float = None
    max: float = None

    def as_dict(self) -> Dict[str, Any]:
        return {"min": self.min, "max": self.max}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Range":
        min_ = dct.get("min", None)
        max_ = dct.get("max", None)
        return cls(min=min_, max=max_)


@dataclass
class ChannelData(Serializable):
    range: Range
    color: Color

    def as_dict(self) -> Dict[str, Any]:
        return {"range": self.range.as_dict(), "color": self.color.as_dict()}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "ChannelData":
        range_ = dct.get("range", Range.from_dict({}))
        color = dct.get("color", Color.from_dict({}))
        return cls(range=range_, color=color)


@dataclass
class Image(Serializable):
    """
    An Image is a list of Pyramids, with an optional background Pyramid.
    The background Pyramid appears in microscopes that obtain a low-resolution image of
    the entire slide, often during a tissue detection step.
    """

    relpath: Path
    block_name: str = ""
    panel_name: str = ""
    pixels: Optional[PyramidGroup] = None
    annotations: List[Annotation] = field(default_factory=list)
    channels_data: List[ChannelData] = field(default_factory=list)

    images_dir = "images"
    log = logging.getLogger(__name__)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "relpath": str(self.relpath),
            "block_name": self.block_name,
            "panel_name": self.panel_name,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Image":
        relpath = dct.get("relpath", None)
        if relpath is None:
            raise RuntimeError("No relpath found")
        relpath = Path(relpath)

        block_name = dct.get("block_name", "")
        panel_name = dct.get("panel_name", "")

        channels_data = dct.get("channels_data", [])
        return cls(
            relpath=relpath,
            block_name=block_name,
            panel_name=panel_name,
            channels_data=channels_data,
        )

    def move(self, basepath: Path, dst_relpath: Path) -> None:
        im_src = basepath / Image.images_dir / self.relpath
        im_dst = basepath / Image.images_dir / dst_relpath

        im_dst.parent.mkdir(parents=True, exist_ok=True)
        im_src.rename(im_dst)
        # if is_dir_empty(im_src.parent):
        #     im_src.parent.rmdir()

        self.relpath = dst_relpath

        # TODO: add annotation rename support

    # def delete(self, basepath: Path) -> None:
    #     image = basepath / Image.images_dir / self.relpath
    #     image.unlink(missing_ok=True)
    #
    # #     TODO: add annotation delete support

    def exists(self, basepath: Path) -> bool:
        return (basepath / Image.images_dir / self.relpath).exists()

    def load(self, basepath: Path) -> None:
        if self.pixels is None:
            self.log.debug(f"Loading {self.relpath}")
            self.pixels = normalize(basepath / Image.images_dir / self.relpath)
            self.log.debug(f"Load {self.relpath} complete")
        else:
            self.log.debug(f"{self.relpath}: Pixels already loaded")

        annotations_dir = basepath / Annotation.annotations_dir / self.relpath.parent
        annotations_dir.mkdir(parents=True, exist_ok=True)
        self.annotations = []  # TODO: load annotations here


def parse_svs_metadata(s: str):
    """
    The metadata contained in SVS files generated by Leica brightfield microscopes is
    the name of the library used to generate the file, followed by a newline, followed
    by a pipe-separated list of values. The first element in the list contains general
    info about the image, and the remaining values are key-value pairs separated by
    equals signs.
    """
    library, info = s.split("\n")
    library = library.strip()
    info = info.split("|")

    general = info[0]
    pairs = [p.split("=") for p in info[1:]]
    properties = {k.strip(): v.strip() for k, v in pairs}

    # try and parse numerical values (at least for now)
    for key, value in properties.items():
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
            else:
                properties[key] = value
        else:
            properties[key] = value

    return {"library": library, "general": general, **properties}


def create_store(path: Path, name: str, level: int) -> ZarrTiffStore:
    with TiffFile(str(path)) as file:
        series: List[TiffPageSeries] = file.series
        series: TiffPageSeries = next(s for s in series if s.name == name)
        return series.aszarr(level)


def get_svs_layers(path: Path, series: TiffPageSeries) -> List[da.Array]:
    store: ZarrTiffStore = series.aszarr()
    group: Group = zarr.open(store, mode="r")
    levels: List[Dict[str, str]] = group.attrs["multiscales"][0]["datasets"]

    pyramid: List[da.Array] = []
    for level in levels:
        # create individual stores for each level to get around lock
        _store: ZarrTiffStore = create_store(path, series.name, int(level["path"]))
        array: da.Array = da.from_zarr(_store, chunks=("auto", "auto", "auto"))
        pyramid.append(array)

    # pyramid: List[da.Array] = [
    #     da.from_zarr(store, component=level["path"], chunks=("auto", "auto", 1))
    #     for level in levels
    # ]

    return pyramid


def get_scn_pyramids(
        path: Path, metadata: ET.Element, series: List[TiffPageSeries]
) -> List[Pyramid]:
    """
    SCN files contain metadata in OME-XML format.
    """

    pyramids: List[Pyramid] = []
    names: List[str] = [s.name for s in series]
    for name in names:
        image_node: ET.Element = metadata.find(f'.//{NS_SCN}image[@name="{name}"]')
        view_node: ET.Element = image_node.find(f".//{NS_SCN}view")

        physical_size = PointF(
            str2int(view_node.get("sizeX")) / 1000,
            str2int(view_node.get("sizeY")) / 1000,
        )

        physical_offset = PointF(
            str2int(view_node.get("offsetX")) / 1000,
            str2int(view_node.get("offsetY")) / 1000,
        )

        pixels_node: ET.Element = image_node.find(f".//{NS_SCN}pixels")
        pixel_size = PointF(
            str2int(pixels_node.get("sizeX")), str2int(pixels_node.get("sizeY"))
        )

        # could override `__div__` in `Point` class... this only appears once though
        mpp = PointF(physical_size.x / pixel_size.x, physical_size.y / pixel_size.y)

        store: ZarrTiffStore = next(s for s in series if s.name == name).aszarr()
        group: Group = zarr.open(store, mode="r")
        levels: List[Dict[str, str]] = group.attrs["multiscales"][0]["datasets"]

        pyramid: List[da.Array] = []
        for level in levels:
            # create individual stores for each level to get around lock
            _store = create_store(path, name, int(level["path"]))
            array = da.from_zarr(_store, chunks=("auto", "auto", "auto"))
            pyramid.append(array)

        # pyramid: List[da.Array] = [
        #     da.from_zarr(store, component=level["path"], chunks=(1, "auto", "auto"))
        #     for level in levels
        # ]

        pyramids.append(Pyramid(layers=pyramid, mpp=mpp, offset=physical_offset))

    return pyramids


def normalize(path: Path) -> Optional[PyramidGroup]:
    with TiffFile(str(path)) as file:
        flags: Set[str] = file.flags
        series: List[TiffPageSeries] = file.series
        pages: List[TiffPage] = file.pages

        scn_metadata = file.scn_metadata

    if "svs" in flags:
        # get metadata
        metadata: Dict[str, Any] = parse_svs_metadata(pages[0].description)

        # get label
        label: np.ndarray = next(s for s in series if s.name == "Label").asarray()

        # get pyramids
        image: TiffPageSeries = next(s for s in series if s.name == "Baseline")
        pyramids = [
            Pyramid(
                layers=get_svs_layers(path, image),
                mpp=PointF(metadata["MPP"], metadata["MPP"]),
                offset=PointF(0, 0),
            )
        ]

        axes: str = image.axes
        channel_index: int = list(axes).index("S")

        return PyramidGroup(
            dtype=image.dtype,
            channel_index=channel_index,
            n_channels=image.shape[channel_index],
            axes=axes,
            file_format="svs",
            flags=flags,
            label=label,
            pyramids=pyramids,
        )

    elif "scn" in flags:
        # get metadata
        metadata: ET.Element = ET.fromstring(scn_metadata)

        # get label
        label_ifd = int(
            metadata.find(f".//{NS_SCN}supplementalImage[@type='label']").get("ifd")
        )
        label = next(p for p in pages if p.index == label_ifd).asarray()

        sources = {
            metadata.find(
                f'.//{NS_SCN}image[@name="{s.name}"]' f"//{NS_SCN}illuminationSource"
            ).text
            for s in series
        }

        if "fluorescence" in sources:
            # is fluorescence image
            series = [s for s in series if s.axes == "CYX"]
            axes = series[0].axes
            channel_index = list(axes).index("C")
            n_channels = series[0].shape[channel_index]
            pyramids = get_scn_pyramids(path, metadata, series)

            return PyramidGroup(
                dtype=series[0].dtype,
                channel_index=channel_index,
                n_channels=n_channels,
                axes=axes,
                file_format="scn",
                flags=flags,
                label=label,
                pyramids=pyramids,
            )

        else:
            # is brightfield image (until we start using other modalities)
            axes = series[0].axes
            channel_index = list(axes).index("S")
            n_channels = series[0].shape[channel_index]
            pyramids = get_scn_pyramids(path, metadata, series)

            return PyramidGroup(
                dtype=series[0].dtype,
                channel_index=channel_index,
                n_channels=n_channels,
                axes=axes,
                file_format="scn",
                flags=flags,
                label=label,
                pyramids=pyramids[1:],  # first pyramid is background pyramid
                background=pyramids[0],  # background pyramid
            )


def get_pr_image_relpaths(basepath: Path, ext=(".svs", ".scn")) -> List[Path]:
    images_dirpath = basepath / Image.images_dir

    filepaths: List[Path] = []
    for root, dirs, files in os.walk(images_dirpath):
        root = Path(root)
        for file in files:
            if file.endswith(ext):
                filepaths.append(root / file)

    relpaths: List[Path] = [
        filepath.relative_to(images_dirpath) for filepath in filepaths
    ]
    filenames: List[str] = [rp.name for rp in relpaths]
    filenames_as_set: Set[str] = set(filenames)

    duplicates: List[str] = []
    for filename in filenames_as_set:
        if filenames.count(filename) > 1:
            duplicates.append(filename)

    if len(duplicates) > 0:
        raise RuntimeError(f'Duplicates found! {"; ".join(duplicates)}"')

    return relpaths
