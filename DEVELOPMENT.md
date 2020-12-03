# Notes
We use conda for managing python versions and dependencies. Install miniconda [from here](https://docs.conda.io/en/latest/miniconda.html).

# Common commands

| Action                        | Command                                             |
| ----------------------------- | --------------------------------------------------- |
| update conda                  | `conda update --name base --channel defaults conda` |
| init conda env                | `conda env create [--file=environment.yml]`         |
| update conda env              | `bin/conda-update.sh`                               |
| activate/deactivate conda env | `conda activate broadside; ...; conda deactivate`   |
| package into executable       | `bin/build.sh`                                      |
| test                          | `pytest`                                            |

## Git

[See here](https://gist.github.com/c0ldlimit/4089101) for adding existing projects to github.

## Testing

Execute `pytest` in the project directory.

# Paradigms
Personally, I've found it difficult to try and refactor methods that form the backend 
of a user interface out into something else, like a set of static methods. This is 
especially true even for the backend-heavy `ProjectModel` class. It's certainly 
possible, but doing so only shuffles the complexity around instead of making it more 
manageable.

If it does get that complex though, one idea would be to have a `ProjectState` class 
that completely defines the state, a `Mutations` class of static methods with state 
mutations, and a `QObject` subclass that handles signals from the model to the view.
That would certainly make things a bit cleaner.

# Version constraints

- PySide2 throws a `SIGSEGV` with python 3.8 specifically.
- Importing vispy throws an import error with python 3.9 (but should be fixed soon: see [here](https://github.com/vispy/vispy/issues/1947))

# Model-View Structure

The layout of views and associated models should be structured like a tree, and events
should propagate along its branches. If two nodes that aren't direct descendants pass
events to each other, that may quickly get difficult to manage.