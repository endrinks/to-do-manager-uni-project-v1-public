"""pytest-Tests für die Todo-Liste.

Der Schwerpunkt liegt auf der Functional-Core-Logik aus todo.py. Jeder Test
prüft genau einen Sachverhalt. Neben dem Happy Path werden Fehler- und
Randfälle abgedeckt. Konsolen-Input wird per unittest.mock.patch isoliert.
"""

from unittest.mock import patch

import pytest

from todo import (
    BANNER,
    DESCRIPTION_MAX_LENGTH,
    HELP_TEXT,
    QuitException,
    ValidationException,
    add_todo,
    create_todo,
    delete_todo,
    execute_command,
    find_todo_by_id,
    format_help,
    format_todos,
    get_input_from_user,
    is_valid_command,
    is_valid_id,
    mark_todo_done,
    parse_command,
    raise_quit_exception_on_quit,
    suggest_command,
    run_todo_app,
    to_id,
    validate_description,
)


# ---------- ID-Validierung ----------

def test_is_valid_id_accepts_positive_integer():
    assert is_valid_id("1") is True
    assert is_valid_id("42") is True


def test_is_valid_id_rejects_text():
    assert is_valid_id("abc") is False
    assert is_valid_id("1a") is False


def test_is_valid_id_rejects_negative_number():
    assert is_valid_id("-1") is False


def test_is_valid_id_rejects_zero():
    assert is_valid_id("0") is False


def test_is_valid_id_rejects_empty_and_whitespace():
    assert is_valid_id("") is False
    assert is_valid_id("   ") is False


def test_to_id_converts_text_to_integer():
    assert to_id("5") == 5
    assert to_id("  7  ") == 7


def test_to_id_rejects_invalid_inputs():
    for invalid in ("abc", "-1", "0", "", "1.5"):
        with pytest.raises(ValidationException):
            to_id(invalid)


# ---------- Befehls-Validierung & Parser ----------

def test_is_valid_command_accepts_known_commands():
    for command in ("add", "list", "done", "delete", "help", "quit"):
        assert is_valid_command(command) is True


def test_is_valid_command_rejects_unknown_command():
    assert is_valid_command("foo") is False
    assert is_valid_command("") is False


def test_suggest_command_suggests_add_for_typo():
    assert suggest_command("ad") == "add"
    assert suggest_command("adddd") == "add"


def test_suggest_command_suggests_delete_for_typo():
    assert suggest_command("delet") == "delete"


def test_suggest_command_suggests_help_for_typo():
    assert suggest_command("hel") == "help"


def test_suggest_command_returns_none_for_very_different_text():
    assert suggest_command("xyzzz") is None
    assert suggest_command("") is None


def test_parse_add_command():
    command, argument = parse_command("add Einkaufen gehen")
    assert command == "add"
    assert argument == "Einkaufen gehen"


def test_parse_list_command():
    command, argument = parse_command("list")
    assert command == "list"
    assert argument == ""


def test_parse_done_command():
    command, argument = parse_command("done 1")
    assert command == "done"
    assert argument == "1"


def test_parse_delete_command():
    command, argument = parse_command("delete 2")
    assert command == "delete"
    assert argument == "2"


def test_parse_quit_command():
    command, argument = parse_command("quit")
    assert command == "quit"
    assert argument == ""


def test_parse_help_command():
    command, argument = parse_command("help")
    assert command == "help"
    assert argument == ""


def test_parse_empty_input_raises_validation_exception():
    with pytest.raises(ValidationException):
        parse_command("")
    with pytest.raises(ValidationException):
        parse_command("   ")


def test_parse_unknown_command_raises_validation_exception():
    with pytest.raises(ValidationException):
        parse_command("foobar 123")


def test_parse_unknown_command_includes_suggestion_in_message():
    with pytest.raises(ValidationException) as excinfo:
        parse_command("ad Milch")
    message = str(excinfo.value)
    assert "Meintest du" in message
    assert "add" in message


def test_parse_unknown_command_without_suggestion_still_hints_help():
    with pytest.raises(ValidationException) as excinfo:
        parse_command("xyzzz")
    assert "help" in str(excinfo.value)


# ---------- validate_description ----------

def test_validate_description_strips_and_returns_cleaned():
    assert validate_description("  Einkaufen  ") == "Einkaufen"


def test_validate_description_rejects_empty():
    with pytest.raises(ValidationException):
        validate_description("")


def test_validate_description_rejects_whitespace_only():
    with pytest.raises(ValidationException):
        validate_description("   ")


def test_validate_description_rejects_too_long():
    too_long = "x" * (DESCRIPTION_MAX_LENGTH + 1)
    with pytest.raises(ValidationException) as excinfo:
        validate_description(too_long)
    assert str(DESCRIPTION_MAX_LENGTH) in str(excinfo.value)


def test_validate_description_accepts_exact_max_length():
    exact = "x" * DESCRIPTION_MAX_LENGTH
    assert validate_description(exact) == exact


def test_validate_description_rejects_control_characters():
    for control in ("\n", "\t", "\r", "\x00"):
        with pytest.raises(ValidationException):
            validate_description(f"hallo{control}welt")


def test_validate_description_accepts_umlauts_and_punctuation():
    assert validate_description("Übung für Müller: Cafés? Ja!") == \
        "Übung für Müller: Cafés? Ja!"


# ---------- create_todo / add_todo ----------

def test_create_todo_returns_open_status_dict():
    todo = create_todo(1, "Test")
    assert todo == {"id": 1, "description": "Test", "status": "open"}


def test_add_todo_creates_open_todo():
    todos = []
    todo, next_id = add_todo(todos, 1, "Einkaufen")
    assert todo["id"] == 1
    assert todo["description"] == "Einkaufen"
    assert todo["status"] == "open"
    assert next_id == 2
    assert todos == [todo]


def test_add_todo_assigns_automatic_id():
    todos = []
    _, next_id = add_todo(todos, 1, "A")
    _, next_id = add_todo(todos, next_id, "B")
    _, next_id = add_todo(todos, next_id, "C")
    assert [t["id"] for t in todos] == [1, 2, 3]
    assert next_id == 4


def test_add_todo_rejects_empty_description():
    with pytest.raises(ValidationException):
        add_todo([], 1, "")


def test_add_todo_rejects_whitespace_only_description():
    with pytest.raises(ValidationException):
        add_todo([], 1, "    ")


def test_add_todo_strips_description_whitespace():
    todos = []
    todo, _ = add_todo(todos, 1, "   Aufräumen   ")
    assert todo["description"] == "Aufräumen"


def test_add_todo_rejects_overlong_description():
    with pytest.raises(ValidationException):
        add_todo([], 1, "x" * (DESCRIPTION_MAX_LENGTH + 1))


def test_add_todo_rejects_control_characters_in_description():
    with pytest.raises(ValidationException):
        add_todo([], 1, "abc\ndef")


# ---------- find / list / format ----------

def test_find_todo_by_id_returns_match():
    todos = [{"id": 1, "description": "A", "status": "open"}]
    assert find_todo_by_id(todos, 1) is todos[0]


def test_find_todo_by_id_returns_none_when_missing():
    assert find_todo_by_id([], 99) is None


def test_format_todos_returns_no_tasks_message_for_empty_list():
    assert format_todos([]) == "keine Aufgaben vorhanden"


def test_format_todos_renders_table_with_header_and_separator():
    todos = [
        {"id": 1, "description": "Einkaufen gehen", "status": "open"},
        {"id": 2, "description": "Python lernen", "status": "done"},
    ]
    result = format_todos(todos)
    lines = result.split("\n")
    assert len(lines) == 4  # Header + Separator + 2 Aufgaben
    assert "ID" in lines[0]
    assert "Beschreibung" in lines[0]
    assert "Status" in lines[0]
    assert set(lines[1]) <= {"-", "+"}  # Separator besteht nur aus - und +
    assert "1" in lines[2] and "Einkaufen gehen" in lines[2] and "open" in lines[2]
    assert "2" in lines[3] and "Python lernen" in lines[3] and "done" in lines[3]


def test_format_todos_pads_columns_to_align():
    todos = [
        {"id": 1, "description": "Einkaufen gehen", "status": "open"},
        {"id": 2, "description": "Python lernen", "status": "done"},
    ]
    result = format_todos(todos)
    lines = result.split("\n")
    # Alle Zeilen sollen gleich lang sein (visuelle Ausrichtung).
    assert len(set(len(line) for line in lines)) == 1


# ---------- format_help ----------

def test_format_help_lists_all_commands():
    text = format_help()
    for command in ("add", "list", "done", "delete", "help", "quit"):
        assert command in text


def test_help_text_constant_matches_format_help():
    assert format_help() == HELP_TEXT


# ---------- done ----------

def test_mark_todo_done_sets_status_to_done():
    todos = [{"id": 1, "description": "Einkaufen", "status": "open"}]
    mark_todo_done(todos, 1)
    assert todos[0]["status"] == "done"


def test_mark_todo_done_unknown_id_raises_validation_exception():
    todos = [{"id": 1, "description": "Einkaufen", "status": "open"}]
    with pytest.raises(ValidationException):
        mark_todo_done(todos, 99)


# ---------- delete ----------

def test_delete_todo_removes_todo():
    todos = [
        {"id": 1, "description": "A", "status": "open"},
        {"id": 2, "description": "B", "status": "open"},
    ]
    delete_todo(todos, 1)
    assert [t["id"] for t in todos] == [2]


def test_delete_unknown_todo_raises_validation_exception():
    with pytest.raises(ValidationException):
        delete_todo([], 1)


# ---------- quit ----------

def test_raise_quit_exception_on_quit():
    with pytest.raises(QuitException):
        raise_quit_exception_on_quit("quit")


def test_raise_quit_exception_on_quit_does_not_raise_for_other_text():
    raise_quit_exception_on_quit("list")
    raise_quit_exception_on_quit("")


# ---------- Input-Mocking ----------

def test_get_input_from_user_with_patch():
    with patch("builtins.input", return_value="add Lesen"):
        assert get_input_from_user("> ") == "add Lesen"


def test_get_input_from_user_with_monkeypatch(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "list")
    assert get_input_from_user("> ") == "list"


def test_get_input_from_user_raises_quit_exception_on_quit():
    # Calculator-Muster aus der Vorlesung: der Quit-Pfad ist im Input-Wrapper gekapselt.
    with patch("builtins.input", return_value="quit"):
        with pytest.raises(QuitException):
            get_input_from_user("> ")


# ---------- execute_command ----------

def test_execute_command_add_returns_message_and_advances_id():
    todos = []
    message, next_id = execute_command("add Einkaufen gehen", todos, 1)
    assert message == "Aufgabe hinzugefügt mit ID 1"
    assert next_id == 2
    assert todos[0]["description"] == "Einkaufen gehen"


def test_execute_command_list_on_empty_returns_no_tasks_message():
    message, next_id = execute_command("list", [], 1)
    assert message == "keine Aufgaben vorhanden"
    assert next_id == 1


def test_execute_command_list_returns_formatted_table():
    todos = [{"id": 1, "description": "A", "status": "open"}]
    message, _ = execute_command("list", todos, 2)
    assert "ID" in message
    assert "A" in message
    assert "open" in message


def test_execute_command_done_marks_todo_done_and_returns_message():
    todos = [{"id": 1, "description": "A", "status": "open"}]
    message, next_id = execute_command("done 1", todos, 2)
    assert message == "Aufgabe 1 wurde erledigt"
    assert todos[0]["status"] == "done"
    assert next_id == 2


def test_execute_command_delete_removes_todo_and_returns_message():
    todos = [{"id": 1, "description": "A", "status": "open"}]
    message, next_id = execute_command("delete 1", todos, 2)
    assert message == "Aufgabe 1 wurde gelöscht"
    assert todos == []
    assert next_id == 2


def test_execute_command_quit_raises_quit_exception():
    with pytest.raises(QuitException):
        execute_command("quit", [], 1)


def test_execute_command_help_returns_help_text():
    message, next_id = execute_command("help", [], 1)
    assert message == HELP_TEXT
    assert next_id == 1


def test_execute_command_help_rejects_extra_argument():
    with pytest.raises(ValidationException):
        execute_command("help me", [], 1)


def test_execute_command_list_rejects_extra_argument():
    with pytest.raises(ValidationException):
        execute_command("list extra", [], 1)


def test_execute_command_quit_rejects_extra_argument():
    with pytest.raises(ValidationException):
        execute_command("quit now", [], 1)


def test_execute_command_done_without_id_raises_validation_exception():
    with pytest.raises(ValidationException):
        execute_command("done", [], 1)


def test_execute_command_delete_without_id_raises_validation_exception():
    with pytest.raises(ValidationException):
        execute_command("delete", [], 1)


def test_execute_command_done_with_invalid_id_raises_validation_exception():
    with pytest.raises(ValidationException):
        execute_command("done abc", [], 1)


def test_execute_command_delete_with_zero_id_raises_validation_exception():
    with pytest.raises(ValidationException):
        execute_command("delete 0", [], 1)


def test_execute_command_done_unknown_id_raises_validation_exception():
    todos = [{"id": 1, "description": "A", "status": "open"}]
    with pytest.raises(ValidationException):
        execute_command("done 99", todos, 2)


def test_execute_command_unknown_command_raises_validation_exception():
    with pytest.raises(ValidationException):
        execute_command("foo bar", [], 1)


def test_execute_command_empty_input_raises_validation_exception():
    with pytest.raises(ValidationException):
        execute_command("", [], 1)


def test_execute_command_typo_returns_suggestion():
    with pytest.raises(ValidationException) as excinfo:
        execute_command("ad Milch", [], 1)
    assert "add" in str(excinfo.value)


def test_execute_command_add_rejects_overlong_description():
    with pytest.raises(ValidationException):
        execute_command("add " + "x" * (DESCRIPTION_MAX_LENGTH + 1), [], 1)


# ---------- BANNER ----------

def test_banner_mentions_all_commands():
    for command in ("add", "list", "done", "delete", "help", "quit"):
        assert command in BANNER


# ---------- ID-Eindeutigkeit ----------

def test_deleted_id_is_not_reused():
    todos = []
    _, next_id = add_todo(todos, 1, "A")
    _, next_id = add_todo(todos, next_id, "B")
    delete_todo(todos, 2)
    _, next_id = add_todo(todos, next_id, "C")
    ids = [t["id"] for t in todos]
    assert ids == [1, 3]
    assert 2 not in ids
    assert next_id == 4


def test_done_does_not_change_next_id():
    todos = []
    _, next_id = add_todo(todos, 1, "A")
    mark_todo_done(todos, 1)
    _, next_id_after = add_todo(todos, next_id, "B")
    assert todos[1]["id"] == 2
    assert next_id_after == 3

# ---------- Zusatzargumente bei done/delete ----------

def test_execute_command_done_with_extra_argument_raises_validation_exception():
    todos = [{"id": 1, "description": "A", "status": "open"}]
    with pytest.raises(ValidationException):
        execute_command("done 1 extra", todos, 2)
    assert todos[0]["status"] == "open"  # Zustand unverändert


def test_execute_command_delete_with_extra_argument_raises_validation_exception():
    todos = [{"id": 1, "description": "A", "status": "open"}]
    with pytest.raises(ValidationException):
        execute_command("delete 1 extra", todos, 2)
    assert len(todos) == 1  # Zustand unverändert


# ---------- End-zu-End: run_todo_app mit gemocktem Input und capsys ----------

def test_run_todo_app_full_session(monkeypatch, capsys):
    """Simuliert eine komplette Sitzung: Eingaben als Sequenz, Ausgabe via capsys.

    Setzt die in spec/validations.pdf Abschnitt 9 beschriebene Strategie um.
    """
    inputs = iter([
        "add Einkaufen gehen",
        "add Python lernen",
        "list",
        "done 1",
        "delete 2",
        "list",
        "quit",
    ])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    run_todo_app()
    output = capsys.readouterr().out
    assert "Aufgabe hinzugefügt mit ID 1" in output
    assert "Aufgabe hinzugefügt mit ID 2" in output
    assert "Aufgabe 1 wurde erledigt" in output
    assert "Aufgabe 2 wurde gelöscht" in output
    assert "Einkaufen gehen" in output
    assert "done" in output
    assert "Bye!" in output


def test_run_todo_app_recovers_from_invalid_input(monkeypatch, capsys):
    """Fehlerhafte Eingaben beenden die Schleife nicht (Spec Abschnitt 1.4)."""
    inputs = iter(["foo", "ad Milch", "done 99", "quit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    run_todo_app()
    output = capsys.readouterr().out
    assert "Unbekannter Befehl 'foo'" in output
    assert "Meintest du: add?" in output
    assert "Aufgabe mit ID 99 wurde nicht gefunden" in output
    assert "Bye!" in output


def test_run_todo_app_handles_eof(monkeypatch, capsys):
    """Strg+D / geschlossener stdin beendet das Programm sauber mit 'Bye!'."""
    def raise_eof(prompt):
        raise EOFError
    monkeypatch.setattr("builtins.input", raise_eof)
    run_todo_app()
    assert "Bye!" in capsys.readouterr().out
