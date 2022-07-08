from typer import Typer, echo
from .src.taskview import TaskView
from typing import List

main = Typer()


@main.command()
def taskview(gui: List[str]) -> Typer:
    if len(gui) > 3:
        raise Exception(f"Too many arguments")
    if len(gui) == 1:
        TaskView().view(gui)
    TaskView().view(gui)