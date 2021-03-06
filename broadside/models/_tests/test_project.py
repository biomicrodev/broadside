# TODO: redo entire testing suite
#
# import json
# from pathlib import Path
#
# from py.path import local
#
# from ...components.viewermodel import ViewerModel
#
#
# def test_project_model():
#     model = ViewerModel()
#
#     expected_state = {
#         "path": None,
#         "name": "",
#         "isStale": False,
#         "description": "",
#     }
#     assert model.as_dict() == expected_state
#
#
# def test_project_model_set_path(tmpdir: local):
#     path = Path(tmpdir.mkdir("my_project"))
#
#     model = ProjectModel()
#     model.path = path
#
#     expected_state = {
#         "path": path,
#         "name": "my_project",
#         "isStale": False,
#         "description": "",
#     }
#     assert model.as_dict() == expected_state
#
#
# def test_project_model_description_set(tmpdir: local):
#     path = Path(tmpdir.mkdir("my_project"))
#
#     model = ProjectModel()
#     model.path = path
#     model.description = "A description of my project"
#
#     expected_state = {
#         "path": path,
#         "name": "my_project",
#         "isStale": True,
#         "description": "A description of my project",
#     }
#     assert model.as_dict() == expected_state
#
#
# def test_project_model_change_project(tmpdir: local):
#     path = Path(tmpdir.mkdir("my_project"))
#     path2 = Path(tmpdir.mkdir("another_project"))
#
#     model = ProjectModel()
#     model.askSave.connect(
#         lambda newPath: model.onSaveResponse(newPath=newPath, action=SaveAction.Cancel)
#     )
#
#     model.path = path
#     model.path = path2
#
#     expected_state = {
#         "path": path,
#         "name": "my_project",
#         "isStale": False,
#         "description": "",
#     }
#     assert model.as_dict() == expected_state
#
#
# def test_project_model_discard_project(tmpdir: local):
#     path = Path(tmpdir.mkdir("my_project"))
#     path2 = Path(tmpdir.mkdir("my_project2"))
#
#     model = ProjectModel()
#     model.askSave.connect(
#         lambda newPath: model.onSaveResponse(newPath=newPath, action=SaveAction.Discard)
#     )
#
#     model.path = path
#     model.path = path2
#
#     expected_state = {
#         "path": path2,
#         "name": "my_project2",
#         "isStale": False,
#         "description": "",
#     }
#     assert model.as_dict() == expected_state
#
#
# def test_project_model_save_project(tmpdir: local):
#     path = Path(tmpdir.mkdir("my_project"))
#     path2 = Path(tmpdir.mkdir("my_project2"))
#
#     model = ProjectModel()
#     model.askSave.connect(
#         lambda newPath: model.onSaveResponse(newPath=newPath, action=SaveAction.Save)
#     )
#
#     model.path = path
#     model.path = path2
#
#     # current state
#     expected_state = {
#         "path": path2,
#         "name": "my_project2",
#         "isStale": False,
#         "description": "",
#     }
#     assert model.as_dict() == expected_state
#
#     # saved settings of previous project
#     expected_settings = {
#         "name": "my_project",
#         "description": "",
#     }
#     with open(path / model.filename, "r") as file:
#         settings = json.load(file)
#
#     assert settings == expected_settings
