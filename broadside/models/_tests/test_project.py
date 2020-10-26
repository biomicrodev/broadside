import json

from py.path import local

from ..project import ProjectModel, SaveAction


def test_project_model():
    model = ProjectModel()

    expected_state = {
        "path": "",
        "name": "",
        "pending_save": False,
        "description": "",
        "images": [],
        "panels": [],
        "devices": [],
        "image_groups": [],
        "task_graph": {},
    }
    assert model.state == expected_state


def test_project_model_set_path(tmpdir: local):
    path = tmpdir.mkdir("my_project")

    model = ProjectModel()
    model.path = path

    expected_state = {
        "path": path,
        "name": "my_project",
        "pending_save": False,
        "description": "",
        "images": [],
        "panels": [],
        "devices": [],
        "image_groups": [],
        "task_graph": {},
    }
    assert model.state == expected_state


def test_project_model_description_set(tmpdir: local):
    path = tmpdir.mkdir("my_project")

    model = ProjectModel()
    model.path = path
    model.description = "A description of my project"

    expected_state = {
        "path": path,
        "name": "my_project",
        "pending_save": True,
        "description": "A description of my project",
        "images": [],
        "panels": [],
        "devices": [],
        "image_groups": [],
        "task_graph": {},
    }
    assert model.state == expected_state


def test_project_model_change_project(tmpdir: local):
    path = tmpdir.mkdir("my_project")
    path2 = tmpdir.mkdir("another_project")

    model = ProjectModel()
    model.events.ask_save.connect(
        lambda event: model.on_save_response(
            new_path=event.new_path, action=SaveAction.Cancel
        )
    )

    model.path = path
    model.path = path2

    expected_state = {
        "path": path,
        "name": "my_project",
        "pending_save": False,
        "description": "",
        "images": [],
        "panels": [],
        "devices": [],
        "image_groups": [],
        "task_graph": {},
    }
    assert model.state == expected_state


def test_project_model_discard_project(tmpdir: local):
    path = tmpdir.mkdir("my_project")
    path2 = tmpdir.mkdir("my_project2")

    model = ProjectModel()
    model.events.ask_save.connect(
        lambda event: model.on_save_response(
            new_path=event.new_path, action=SaveAction.Discard
        )
    )

    model.path = path
    model.path = path2

    expected_state = {
        "path": path2,
        "name": "my_project2",
        "pending_save": False,
        "description": "",
        "images": [],
        "panels": [],
        "devices": [],
        "image_groups": [],
        "task_graph": {},
    }
    assert model.state == expected_state


def test_project_model_save_project(tmpdir: local):
    path = tmpdir.mkdir("my_project")
    path2 = tmpdir.mkdir("my_project2")

    model = ProjectModel()
    model.events.ask_save.connect(
        lambda event: model.on_save_response(
            new_path=event.new_path, action=SaveAction.Save
        )
    )

    model.path = path
    model.path = path2

    # current state
    expected_state = {
        "path": path2,
        "name": "my_project2",
        "pending_save": False,
        "description": "",
        "images": [],
        "panels": [],
        "devices": [],
        "image_groups": [],
        "task_graph": {},
    }
    assert model.state == expected_state

    # saved settings of previous project
    expected_settings = {
        "name": "my_project",
        "description": "",
        "panels": [],
        "devices": [],
        "image_groups": [],
        "task_graph": {},
    }
    with open(path / model.filename, "r") as file:
        settings = json.load(file)

    assert settings == expected_settings
