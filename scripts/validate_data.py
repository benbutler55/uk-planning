#!/usr/bin/env python3
"""Data validation with schema checks, enum enforcement, FK integrity, and unique IDs."""
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


def read_column_values(path: Path, column: str):
    """Read all values for a column from a CSV file."""
    rows, _ = read_csv(path)
    return {(row.get(column, "") or "").strip() for row in rows}


def validate_dataset(spec, all_specs):
    errors = []
    warnings = []
    dataset_path = ROOT / spec["path"]
    if not dataset_path.exists():
        return [f"Missing dataset: {spec['path']}"], []

    rows, columns = read_csv(dataset_path)
    missing = [col for col in spec.get("required_columns", []) if col not in columns]
    if missing:
        errors.append(f"{spec['path']}: missing columns: {', '.join(missing)}")
        return errors, warnings

    # --- Required values ---
    for idx, row in enumerate(rows, start=2):
        for col in spec.get("required_columns", []):
            if not (row.get(col, "") or "").strip():
                errors.append(f"{spec['path']}:{idx} empty required value in '{col}'")

    # --- Date format ---
    for idx, row in enumerate(rows, start=2):
        for col in spec.get("date_columns", []):
            value = (row.get(col, "") or "").strip()
            if value and not DATE_RE.match(value):
                errors.append(
                    f"{spec['path']}:{idx} invalid date '{value}' in '{col}' (expected YYYY-MM-DD)"
                )

    # --- URL format ---
    for idx, row in enumerate(rows, start=2):
        for col in spec.get("url_columns", []):
            value = (row.get(col, "") or "").strip()
            if value and not (value.startswith("https://") or value.startswith("http://")):
                errors.append(f"{spec['path']}:{idx} invalid URL '{value}' in '{col}'")

    # --- Score range ---
    for idx, row in enumerate(rows, start=2):
        for col in spec.get("score_columns", []):
            value = (row.get(col, "") or "").strip()
            try:
                score = float(value)
            except ValueError:
                errors.append(f"{spec['path']}:{idx} non-numeric score '{value}' in '{col}'")
                continue
            if score < 1 or score > 5:
                errors.append(f"{spec['path']}:{idx} score out of range (1-5) for '{col}': {value}")

    # --- Unique IDs ---
    id_col = spec.get("id_column")
    if id_col:
        seen_ids = {}
        for idx, row in enumerate(rows, start=2):
            val = (row.get(id_col, "") or "").strip()
            if val in seen_ids:
                errors.append(
                    f"{spec['path']}:{idx} duplicate {id_col} '{val}' (first seen at row {seen_ids[val]})"
                )
            else:
                seen_ids[val] = idx

    # --- Enum checks ---
    for col, allowed in spec.get("enum_columns", {}).items():
        allowed_lower = {v.lower() for v in allowed}
        for idx, row in enumerate(rows, start=2):
            val = (row.get(col, "") or "").strip()
            if val and val.lower() not in allowed_lower:
                errors.append(
                    f"{spec['path']}:{idx} invalid value '{val}' in '{col}' "
                    f"(allowed: {', '.join(allowed)})"
                )

    # --- Foreign key checks ---
    for col, fk_spec in spec.get("fk_columns", {}).items():
        target_path = ROOT / fk_spec["target_dataset"]
        target_col = fk_spec["target_column"]
        separator = fk_spec.get("multi_value_separator")

        if not target_path.exists():
            warnings.append(
                f"{spec['path']}: FK target missing: {fk_spec['target_dataset']}"
            )
            continue

        valid_ids = read_column_values(target_path, target_col)

        for idx, row in enumerate(rows, start=2):
            raw = (row.get(col, "") or "").strip()
            if not raw:
                continue
            values = raw.split(separator) if separator else [raw]
            for v in values:
                v = v.strip()
                if v and v not in valid_ids:
                    errors.append(
                        f"{spec['path']}:{idx} broken FK in '{col}': "
                        f"'{v}' not found in {fk_spec['target_dataset']}[{target_col}]"
                    )

    return errors, warnings


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    datasets = schema.get("datasets", [])
    all_errors = []
    all_warnings = []

    for dataset in datasets:
        errs, warns = validate_dataset(dataset, datasets)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    if all_warnings:
        print("Warnings:")
        for w in all_warnings:
            print(f"  [warn] {w}")

    if all_errors:
        print("Data validation failed:")
        for err in all_errors:
            print(f"  [error] {err}")
        sys.exit(1)

    print("Data validation passed for all datasets.")


if __name__ == "__main__":
    main()
