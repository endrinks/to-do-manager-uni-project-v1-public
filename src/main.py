"""Eintrittspunkt der Todo-Liste.

Diese Datei enthält bewusst keine Geschäftslogik. Sie startet die in
todo.py implementierte Schleife, damit Start und Logik getrennt bleiben
und die Logik weiter ohne Konsole testbar ist.
"""

from todo import run_todo_app


if __name__ == "__main__":
    run_todo_app()
