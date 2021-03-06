"""
Not sure why, but the entry point for PyInstaller has to be a python script, and it has
to lie within the main project folder. I'm probably misunderstanding how PyInstaller
works, but at least this works for now.
"""

from broadside import run

run()
