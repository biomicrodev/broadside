# Choice of framework
User interface frameworks include `qt`, `wxwidgets`, `Tcl/Tk`, and web-based technologies. Our choice of framework is constrained by [napari](https://github.com/napari/napari), which serves as the renderer for tiled pyramidal images. Napari uses python ports of qt as its user interface. The two major ports are `PySide2` and `PyQt5`; the most significant difference is in their licensing. Because of slight differences in import statements, `qtpy` is a thin abstraction layer that offers consistent import statement styles and allows picking one port over the other.

# Project management
We keep our run, build, and update commands minimal by using only shell or batch files.

# Dependency management
Because of the many dependencies that we foresee as part of this project, we must segregate the python environment from system python.

To manage our dependencies, we have several options:

- `venv` (python's built-in dependency management)
- `conda`
- `poetry`

Currently, we are using [`miniconda`](https://docs.conda.io/en/latest/miniconda.html), but switching to `poetry` may be done soon.

# Versioning
[See here](https://gist.github.com/c0ldlimit/4089101) for adding existing projects to github.

## Version constraints
- PySide2 throws a `SIGSEGV` with python 3.8 specifically.
- Importing vispy throws an import error with python 3.9 (but should be fixed soon: see [here](https://github.com/vispy/vispy/issues/1947))

# Testing
TODO: figure out fuzz testing methods for `PySide2`/`PyQt5`.

# Domain Architecture
The overall application workflow consists of selecting a project path, either populating the UI with an existing config file or creating a new one with default values, and saving it to the config file.

## Terminology
A project defines a self-contained set of histological images and associated metadata. A project is defined by the path to the project folder, which is structured as follows:

```
- my_project/
    - project.json
    - images/
```

Associated metadata include **devices**, **blocks**, and **panels**.

Devices are small parts containing reservoirs on their surfaces, from which formulations diffuse outward.

```
- Project: Dict[str, Any]
    - description: str
    - devices: List[Device]
    - blocks: List[Block]
    - panels: List[Panel]
    - images: List[Image]
    - task_graph: TaskGraph
    
- Device: Dict[str, Any]
    - name: str
    - payload: List[Formulation]
    
- Formulation: Dict[str, Union[str, float]]
    - level: str
    - angle: float [0, 360)
    - name: str
    
- Sample: Dict[str, Any]
    - name: str
    - device_name: str
    
- Panel: Dict[str, Any]
    - name: str
    - modality: str
    - channels: List[Channel]
    
- Channel: Dict[str, Any]
    - biomarker: str
    - chromogen: str
    
- Image: Dict[str, Any]
    - filepath: pathlib.Path
    - block_name: str
    - pyramids: PyramidSet
    - annotations: List[Annotation]

- Annotation: Dict[str, Any]
    - name: str
    - shape...?
    
- PyramidSet: NamedTuple (read-only)
    - dtype: numpy.dtype
    - channel_index: int
    - n_channels: int
    - axes: str
    - file_format: str
    - flags: Set[str]
    
    - label: Optional[numpy.ndarray]
    - pyramids: List[Pyramid]
    - background: Optional[Pyramid]
    
- Pyramid: NamedTuple (read-only)
    - layers: List[dask.array.Array]
    - mpp: PointXY
    - offset: PointXY
    - object_sets: List[ObjectSet]
    
- ObjectSet: Dict[str, Any]
    - name: str
    - coords: numpy.ndarray (Nx2) (or geopandas.GeoDataFrame)
    - polygons: numpy.ndarray (Nxk) (or geopandas.GeoDataFrame)
 
- TaskGraph: Dict[Set[str], Any]
```

# Event system
As with most GUI applications, the following systems are required:
- an event system for reacting appropriately to user actions
- a hierarchical model-view-whatever system of widgets responding to and triggering events

Although using Qt's signals and slots system is slightly awkward (having to place them 
as class attributes), the application is small enough that we can utilize them without
any issues. If the application were to grow larger, then a custom event system would be
useful.

# Paradigms
Personally, I've found it difficult to try to refactor methods that form the backend 
of a user interface out into something else, like a set of static methods. This is 
especially true even for the backend-heavy `ProjectModel` class. It's certainly 
possible, but doing so only shuffles the complexity around instead of making it more 
manageable.

If it does get that complex though, one idea would be to have a `ProjectState` class 
that completely defines the state, a `Mutations` class of static methods with state 
mutations, and a `QObject` subclass that handles signals from the model to the view.
That would certainly make things a bit cleaner.

I regret using `dataChanged`. Use a different signal/slot system in the future.

# Model-View Structure
The layout of views and associated models should be structured like a tree, and events
should propagate along its branches. If two nodes that aren't direct descendants pass
events to each other, that may quickly get difficult to manage.

Because the application is not so big, we can get away with structuring reactivity as
follows: load the session state from record state, populate the screen state using the
session state, and all subsequent changes flow from screen to session.
