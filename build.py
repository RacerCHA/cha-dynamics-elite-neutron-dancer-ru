"""Build a localized EDMC plugin ZIP from the unmodified official release."""
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

BASE = Path(__file__).resolve().parent
ORIGINAL_SHA256 = "fc63cb86d8fb28e96e441bd618f42c3b0010f1b6791732ff89b7243ffa425a0d"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def translate(data, change):
    text = data.decode("utf-8").replace("\r\n", "\n")
    if digest(text.encode()) != change["before"]:
        raise ValueError(f"Не совпала исходная версия {change['file']}")
    lines = text.splitlines(keepends=True)
    for start, count, replacement in reversed(change["edits"]):
        lines[start:start + count] = [replacement]
    result = "".join(lines).encode()
    if digest(result) != change["after"]:
        raise ValueError(f"Ошибка проверки перевода {change['file']}")
    return result


def build(original, target):
    if digest(original.read_bytes()) != ORIGINAL_SHA256:
        raise ValueError("Нужен официальный EDMC-NeutronDancer.zip версии 2.1.2.")
    changes = {item["file"]: item for item in json.loads((BASE / "translation.json").read_text("utf-8"))}
    with ZipFile(original) as source, TemporaryFile() as temporary:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as output:
            for entry in source.infolist():
                if entry.is_dir():
                    continue
                name = entry.filename
                data = source.read(entry)
                if name in changes:
                    data = translate(data, changes.pop(name))
                output.writestr("EDMC-NeutronDancer/" + name, data)
        if changes:
            raise ValueError("В исходном архиве отсутствуют файлы перевода.")
        temporary.seek(0)
        with target.open("xb") as out:
            out.write(temporary.read())


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "EDMC-NeutronDancer.zip"
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "EDMC-NeutronDancer-2.1.2-ru.zip"
    try:
        build(source, target)
    except (OSError, ValueError) as error:
        sys.exit(str(error))
    print(f"Готово: {target.name}")
