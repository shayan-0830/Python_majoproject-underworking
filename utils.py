"""Small helpers for console input/output."""
import getpass


def ask(prompt, allow_empty=False):
    while True:
        value = input(prompt).strip()
        if value or allow_empty:
            return value
        print("  Input cannot be empty.")


def ask_password(prompt="Password: "):
    return getpass.getpass(prompt)


def ask_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("  Please enter a whole number.")
            continue
        if (min_val is not None and value < min_val) or (max_val is not None and value > max_val):
            print(f"  Value must be between {min_val} and {max_val}.")
            continue
        return value


def ask_float(prompt, min_val=0.0, max_val=None):
    while True:
        try:
            value = float(input(prompt).strip())
        except ValueError:
            print("  Please enter a number.")
            continue
        if value < min_val or (max_val is not None and value > max_val):
            print(f"  Value must be between {min_val} and {max_val}.")
            continue
        return value


def confirm(prompt):
    return input(f"{prompt} (y/n): ").strip().lower() == "y"


def header(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def fmt_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def print_table(headers, rows):
    if not rows:
        print("  (no records)")
        return
    rows = [[str(c) for c in r] for r in rows]
    widths = [max(len(str(h)), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    line = "  " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("  " + "-+-".join("-" * w for w in widths))
    for r in rows:
        print("  " + " | ".join(c.ljust(w) for c, w in zip(r, widths)))
