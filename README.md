# To Do Manager Uni Project V1

A clean, tested command-line todo manager written in Python.

This project was built as a university assignment with a focus on simple
architecture, clear validation, and testable business logic. The application
keeps the user interface small and separates console input/output from the
functional todo logic.

## Features

- Add new todo items with automatic IDs
- List all tasks in a readable table
- Mark tasks as done
- Delete tasks by ID
- Show built-in help from the CLI
- Validate invalid commands, missing arguments, empty descriptions, long input,
  control characters, and invalid IDs
- Suggest similar commands for small typos
- Keep core logic testable without relying on console input

## Project Structure

```text
.
├── spec/
│   └── validations.pdf
└── src/
    ├── main.py
    ├── todo.py
    └── todo_test.py
```

## Architecture

The implementation follows a small functional-core style:

- `src/main.py` starts the application.
- `src/todo.py` contains validation, parsing, formatting, todo operations, and
  the interactive loop.
- `src/todo_test.py` contains pytest coverage for the core behavior and edge
  cases.

Most business logic is kept separate from console input/output, which makes the
application easier to test, reason about, and extend.

## Requirements

- Python 3
- `pytest` for running the test suite

Install pytest if it is not already available:

```bash
python3 -m pip install pytest
```

## Run the App

From the repository root:

```bash
python3 src/main.py
```

## Commands

```text
add <text>     create a new task
list           show all tasks
done <id>      mark a task as done
delete <id>    delete a task
help           show the command overview
quit           exit the program
```

Example session:

```text
> add Finish portfolio task
Aufgabe hinzugefügt mit ID 1
> list
 ID | Beschreibung           | Status
----+------------------------+------
  1 | Finish portfolio task  | open
> done 1
Aufgabe 1 wurde erledigt
> quit
Bye!
```

## Run Tests

```bash
python3 -m pytest src/todo_test.py
```

## Notes

- Todos are stored in memory for the current program session.
- The project intentionally uses the Python standard library for the app logic.
- Input validation is implemented explicitly to keep behavior predictable and
  easy to verify.
