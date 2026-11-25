"""layout/layout.yaml reader/writer (no PyYAML: neither Blender's Python nor the system Python has it).

The file is plain YAML restricted to the shape in layout/README.md: a top-level map with scalars and one
`items:` list of flat maps. Values are numbers, booleans, null, strings (plain or double-quoted) and inline
lists of numbers. Comments (# ...) and blank lines are allowed anywhere. Any YAML library reads it too.

    import layout_io; data = layout_io.load("layout/layout.yaml"); layout_io.save(data, path)
Works in Blender's Python and in system python3 (stdlib only).
"""
import json
import re

FIELD_ORDER = ["id", "label", "kind", "zone", "pos", "z", "rot", "size", "on", "locked", "machine", "count",
               "note", "objects"]
NUM = re.compile(r"^-?\d+(\.\d+)?([eE][-+]?\d+)?$")


def _scalar(s):
    s = s.strip()
    if s == "" or s in ("null", "~"):
        return None
    if s in ("true", "false"):
        return s == "true"
    if s.startswith('"'):
        return json.loads(s)
    if s.startswith("'"):
        return s[1:-1].replace("''", "'")
    if s.startswith("["):
        inner = s[1:-1].strip()
        if not inner:
            return []
        out, cur, q = [], "", False
        for ch in inner:                        # split on commas outside double quotes
            if ch == '"':
                q = not q
            if ch == "," and not q:
                out.append(_scalar(cur)); cur = ""
            else:
                cur += ch
        out.append(_scalar(cur))
        return out
    if NUM.match(s):
        return float(s) if any(c in s for c in ".eE") else int(s)
    return s


def _strip_comment(line):
    q = False
    for i, ch in enumerate(line):
        if ch == '"':
            q = not q
        elif ch == "#" and not q and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def loads(text):
    data, items, cur = {}, None, None
    for n, raw in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw)
        if not line.strip():
            continue
        ind = len(line) - len(line.lstrip(" "))
        body = line.strip()
        if ind == 0:
            key, _, val = body.partition(":")
            if key == "items":
                items = data["items"] = []
                cur = None
            else:
                data[key.strip()] = _scalar(val)
            continue
        if items is None:
            raise ValueError(f"line {n}: indented line outside items")
        if body.startswith("- "):
            cur = {}
            items.append(cur)
            body = body[2:].strip()
        if cur is None:
            raise ValueError(f"line {n}: item field before '- '")
        if body.startswith('"'):                    # quoted key, e.g. "on": (YAML 1.1 reads bare on as true)
            end = body.index('"', 1)
            key, rest = body[1:end], body[end + 1:]
            sep, val = (":", rest.split(":", 1)[1]) if ":" in rest else ("", "")
        else:
            key, sep, val = body.partition(":")
        if not sep:
            raise ValueError(f"line {n}: expected 'key: value'")
        cur[key.strip()] = _scalar(val)
    return data


def load(path):
    with open(path, encoding="utf-8") as f:
        return loads(f.read())


def _fmt(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        s = ("%.3f" % v).rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, int):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_fmt(x) for x in v) + "]"
    s = str(v)
    if s == "" or not re.match(r"^[A-Za-z0-9_./-][A-Za-z0-9 _./()+-]*$", s) or s in ("true", "false", "null") \
            or NUM.match(s) or s.endswith(" "):
        return json.dumps(s, ensure_ascii=False)
    return s


def dumps(data, header=""):
    out = [header.rstrip()] if header else []
    for k, v in data.items():
        if k != "items":
            out.append(f"{k}: {_fmt(v)}")
    out.append("items:")
    for it in data.get("items", []):
        keys = [k for k in FIELD_ORDER if k in it] + [k for k in it if k not in FIELD_ORDER]
        first = True
        for k in keys:
            if it[k] is None and k not in ("id",):
                continue
            kk = f'"{k}"' if k in ("on", "off", "yes", "no", "y", "n") else k
            out.append(("  - " if first else "    ") + f"{kk}: {_fmt(it[k])}")
            first = False
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def save(data, path, header=""):
    with open(path, "w", encoding="utf-8") as f:
        f.write(dumps(data, header))
