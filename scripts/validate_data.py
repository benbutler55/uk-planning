#!/usr/bin/env python3
import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "data/schemas/datasets.json"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return rows, reader.fieldnames or []


def validate_dataset(spec):
    errors = []
    dataset_path = ROOT / spec["path"]
    if not dataset_path.exists():
        return [f"Missing dataset: {spec['path']}"]

    rows, columns = read_csv(dataset_path)
    missing = [col for col in spec.get("required_columns", []) if col not in columns]
    if missing:
        errors.append(f"{spec['path']}: missing columns: {', '.join(missing)}")
        return errors

    for idx, row in enumerate(rows, start=2):
        for col in spec.get("required_columns", []):
            if not (row.get(col, "") or "").strip():
                errors.append(f"{spec['path']}:{idx} empty required value in '{col}'")

        for col in spec.get("date_columns", []):
            value = (row.get(col, "") or "").strip()
            if value and not DATE_RE.match(value):
                errors.append(f"{spec['path']}:{idx} invalid date '{value}' in '{col}' (expected YYYY-MM-DD)")

        for col in spec.get("url_columns", []):
            value = (row.get(col, "") or "").strip()
            if value and not (value.startswith("https://") or value.startswith("http://")):
                errors.append(f"{spec['path']}:{idx} invalid URL '{value}' in '{col}'")

        for col in spec.get("score_columns", []):
            value = (row.get(col, "") or "").strip()
            try:
                score = float(value)
            except ValueError:
                errors.append(f"{spec['path']}:{idx} non-numeric score '{value}' in '{col}'")
                continue
            if score < 1 or score > 5:
                errors.append(f"{spec['path']}:{idx} score out of range (1-5) for '{col}': {value}")

    return errors


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    all_errors = []
    for dataset in schema.get("datasets", []):
        all_errors.extend(validate_dataset(dataset))

    if all_errors:
        print("Data validation failed:")
        for err in all_errors:
            print(f"- {err}")
        sys.exit(1)

    print("Data validation passed for all datasets.")


if __name__ == "__main__":
    main()
