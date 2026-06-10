"""Functional Core der Todo-Liste.

Enthält alle reinen Logikfunktionen: Validierung, Parser, Todo-Operationen,
Formatierung, Befehlsausführung sowie die Hauptschleife. Input und Output
werden bewusst nur in get_input_from_user und run_todo_app verwendet, damit
die übrige Logik ohne Konsole testbar bleibt.
"""

import difflib

# Statuswerte eines Todos. Konstanten, damit Tippfehler vom Interpreter
# und nicht erst zur Laufzeit gefunden werden.
STATUS_OPEN = "open"
STATUS_DONE = "done"

# Pflichtbefehle der Aufgabenstellung plus 'help' als reine UX-Hilfe.
VALID_COMMANDS = ("add", "list", "done", "delete", "help", "quit")

# Harte Obergrenze, um Copy-Paste-Unfälle und Anzeigeprobleme zu vermeiden.
DESCRIPTION_MAX_LENGTH = 200

# Hilfetext, der beim Befehl 'help' ausgegeben wird.
HELP_TEXT = (
    "Verfuegbare Befehle:\n"
    "  add <text>     neue Aufgabe anlegen\n"
    "  list           alle Aufgaben anzeigen\n"
    "  done <id>      Aufgabe als erledigt markieren\n"
    "  delete <id>    Aufgabe loeschen\n"
    "  help           diese Uebersicht zeigen\n"
    "  quit           Programm beenden"
)

# Startbanner. ASCII-only, damit es in jedem Terminal sauber rendert.
BANNER = (
    "============================================\n"
    "         T O D O - L I S T E\n"
    "============================================\n"
    "Befehle: add | list | done | delete | help | quit"
)


class QuitException(Exception):
    """Wird ausgelöst, wenn der Nutzer das Programm regulär beenden möchte."""


class ValidationException(Exception):
    """Wird bei jeder Form ungültiger Eingabe ausgelöst."""


# ---------- ID-Validierung ----------

def is_valid_id(text):
    """Prüft, ob text eine darstellbare positive ganze Zahl ist."""
    if not isinstance(text, str):
        return False
    stripped = text.strip()
    if not stripped:
        return False
    if not stripped.isdigit():
        return False
    return int(stripped) > 0


def to_id(text):
    """Wandelt text in eine gültige Todo-ID um.

    Wirft ValidationException, falls text keine positive ganze Zahl darstellt.
    """
    if not is_valid_id(text):
        raise ValidationException("Fehler: ID muss eine positive ganze Zahl sein.")
    return int(text.strip())


# ---------- Befehls-Parser ----------

def is_valid_command(command):
    """True, wenn command einer der bekannten Befehle ist."""
    return command in VALID_COMMANDS


def suggest_command(text):
    """Schlägt den nächstliegenden bekannten Befehl vor (oder None).

    Verwendet difflib.get_close_matches – Standardbibliothek, kein extra
    Framework. So bekommt der Nutzer bei 'ad' einen Hinweis auf 'add'.
    """
    if not isinstance(text, str) or not text:
        return None
    matches = difflib.get_close_matches(text.lower(), VALID_COMMANDS, n=1, cutoff=0.6)
    return matches[0] if matches else None


def parse_command(user_input):
    """Zerlegt eine Roheingabe in (command, argument).

    - Leere/whitespace Eingabe -> ValidationException.
    - Unbekannter Befehl -> ValidationException, mit Vorschlag falls ähnlich.
    - Argument ist alles nach dem ersten Wort, beidseitig getrimmt.
    """
    if user_input is None or not user_input.strip():
        raise ValidationException("Fehler: Leere Eingabe.")
    parts = user_input.strip().split(maxsplit=1)
    command = parts[0]
    argument = parts[1].strip() if len(parts) > 1 else ""
    if not is_valid_command(command):
        suggestion = suggest_command(command)
        if suggestion:
            raise ValidationException(
                f"Fehler: Unbekannter Befehl '{command}'. Meintest du: {suggestion}? "
                f"Tippe 'help' fuer eine Uebersicht."
            )
        raise ValidationException(
            f"Fehler: Unbekannter Befehl '{command}'. Tippe 'help' fuer eine Uebersicht."
        )
    return command, argument


# ---------- Beschreibung validieren ----------

def _has_control_chars(text):
    """True, wenn text mindestens ein Steuerzeichen (Code < 32) enthält."""
    return any(ord(ch) < 32 for ch in text)


def validate_description(description):
    """Prüft die Beschreibung und liefert die getrimmte Version zurück.

    Wirft ValidationException bei: leer, zu lang, Steuerzeichen.
    Umlaute und gängige Sonderzeichen sind erlaubt.
    """
    cleaned = description.strip() if description else ""
    if not cleaned:
        raise ValidationException("Fehler: Beschreibung darf nicht leer sein.")
    if len(cleaned) > DESCRIPTION_MAX_LENGTH:
        raise ValidationException(
            f"Fehler: Beschreibung darf hoechstens {DESCRIPTION_MAX_LENGTH} Zeichen "
            f"lang sein (war {len(cleaned)})."
        )
    if _has_control_chars(cleaned):
        raise ValidationException(
            "Fehler: Beschreibung darf keine Steuerzeichen (z.B. Tab, Zeilenumbruch) enthalten."
        )
    return cleaned


# ---------- Todo-Operationen ----------

def create_todo(todo_id, description):
    """Erzeugt ein neues Todo-Dictionary im Status 'open'."""
    return {"id": todo_id, "description": description, "status": STATUS_OPEN}


def add_todo(todos, next_id, description):
    """Fügt ein neues Todo hinzu und liefert (todo, neue_next_id)."""
    cleaned = validate_description(description)
    todo = create_todo(next_id, cleaned)
    todos.append(todo)
    return todo, next_id + 1


def find_todo_by_id(todos, todo_id):
    """Liefert das Todo mit passender ID oder None."""
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    return None


def mark_todo_done(todos, todo_id):
    """Setzt den Status des Todos auf 'done'.

    Wirft ValidationException, wenn kein Todo mit dieser ID existiert.
    """
    todo = find_todo_by_id(todos, todo_id)
    if todo is None:
        raise ValidationException(
            f"Fehler: Aufgabe mit ID {todo_id} wurde nicht gefunden."
        )
    todo["status"] = STATUS_DONE
    return todo


def delete_todo(todos, todo_id):
    """Entfernt das Todo mit todo_id aus todos.

    Wirft ValidationException, wenn kein Todo mit dieser ID existiert.
    """
    todo = find_todo_by_id(todos, todo_id)
    if todo is None:
        raise ValidationException(
            f"Fehler: Aufgabe mit ID {todo_id} wurde nicht gefunden."
        )
    todos.remove(todo)
    return todo


# ---------- Formatierung ----------

def format_todos(todos):
    """Formatiert die Todo-Liste als ASCII-Tabelle mit Header.

    Leere Liste -> 'keine Aufgaben vorhanden'.
    Spaltenbreite passt sich an den längsten Eintrag an.
    """
    if not todos:
        return "keine Aufgaben vorhanden"

    id_w = max(len("ID"), max(len(str(t["id"])) for t in todos))
    desc_w = max(len("Beschreibung"), max(len(t["description"]) for t in todos))
    status_w = max(len("Status"), max(len(t["status"]) for t in todos))

    header = f" {'ID'.rjust(id_w)} | {'Beschreibung'.ljust(desc_w)} | {'Status'.ljust(status_w)}"
    separator = "-" * (id_w + 2) + "+" + "-" * (desc_w + 2) + "+" + "-" * (status_w + 1)
    lines = [header, separator]
    for t in todos:
        lines.append(
            f" {str(t['id']).rjust(id_w)} | "
            f"{t['description'].ljust(desc_w)} | "
            f"{t['status'].ljust(status_w)}"
        )
    return "\n".join(lines)


def format_help():
    """Gibt den Hilfetext zurück."""
    return HELP_TEXT


# ---------- Befehlsausführung ----------

def execute_command(user_input, todos, next_id):
    """Führt einen Befehl aus und liefert (Antworttext, neue_next_id).

    todos wird in-place verändert. Bei 'quit' wird QuitException geworfen,
    bei Validierungsfehlern ValidationException.
    """
    command, argument = parse_command(user_input)

    if command == "add":
        todo, next_id = add_todo(todos, next_id, argument)
        return f"Aufgabe hinzugefügt mit ID {todo['id']}", next_id

    if command == "list":
        if argument:
            raise ValidationException("Fehler: Der Befehl list erwartet kein Argument.")
        return format_todos(todos), next_id

    if command == "done":
        if not argument:
            raise ValidationException(
                "Fehler: Der Befehl done erwartet eine ID als Argument."
            )
        todo_id = to_id(argument)
        mark_todo_done(todos, todo_id)
        return f"Aufgabe {todo_id} wurde erledigt", next_id

    if command == "delete":
        if not argument:
            raise ValidationException(
                "Fehler: Der Befehl delete erwartet eine ID als Argument."
            )
        todo_id = to_id(argument)
        delete_todo(todos, todo_id)
        return f"Aufgabe {todo_id} wurde gelöscht", next_id

    if command == "help":
        if argument:
            raise ValidationException("Fehler: Der Befehl help erwartet kein Argument.")
        return format_help(), next_id

    # command == "quit" — parse_command lässt nur gültige Befehle durch.
    if argument:
        raise ValidationException("Fehler: Der Befehl quit erwartet kein Argument.")
    raise QuitException("Bye!")


def raise_quit_exception_on_quit(text):
    """Wirft QuitException, falls text 'quit' ist (case- und whitespace-tolerant)."""
    if isinstance(text, str) and text.strip() == "quit":
        raise QuitException("Bye!")


# ---------- Imperative Shell (Konsolen-I/O) ----------

def get_input_from_user(prompt):
    """Liest eine Zeile und behandelt 'quit' direkt (Calculator-Muster aus der Vorlesung)."""
    response = input(prompt)
    raise_quit_exception_on_quit(response)
    return response


def run_todo_app():
    """Startet die interaktive Todo-Schleife."""
    todos = []
    next_id = 1
    print(BANNER)
    while True:
        try:
            user_input = get_input_from_user("> ")
            message, next_id = execute_command(user_input, todos, next_id)
            print(message)
        except ValidationException as error:
            print(str(error))
        except QuitException as goodbye:
            print(str(goodbye))
            break
        except EOFError:
            # Strg+D / geschlossener stdin -> sauberes Beenden statt Traceback.
            print("Bye!")
            break
