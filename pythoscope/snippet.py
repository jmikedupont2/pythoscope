"""
The idea is to allow the user to place the following pair of snippets in
the application code. One at the top of the first module to be imported:

import pythoscope
pythoscope.start()

and the second before the application exists:

pythoscope.stop()
"""

import os
import sys

from cmdline import find_project_directory, PythoscopeDirectoryMissing
from execution import Execution
from store import Project
from tracer import Tracer
from inspector.dynamic import Inspector


project = None
tracer = None
inspector = None

def start():
    global project, tracer, inspector
    try:
        project = Project.from_directory(find_project_directory(os.getcwd()))
        execution = Execution(project)
        inspector = Inspector(execution)
        tracer = Tracer(inspector)
        tracer.btracer.setup()
        sys.settrace(tracer.tracer)
    except PythoscopeDirectoryMissing:
        print("Can't find .pythoscope/ directory for this project. "
            "Initialize the project with the '--init' option first. "
            "Pythoscope tracing disabled for this run.")

def stop():
    global project, tracer, inspector
    if project is None or tracer is None or inspector is None:
        return
    sys.settrace(None)
    tracer.btracer.teardown()
    inspector.finalize()
    project.remember_execution_from_snippet(inspector.execution)
    project.save()
    project, tracer, inspector = None, None, None
