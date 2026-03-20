#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"


class A11yParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0
        self.table_stack = []
        self.tables = []
        self.controls = []
        self.label_depth = 0
        self.labels_for = set()
        self.has_lang = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.has_lang = True
        if tag == "h1":
            self.h1_count += 1
        if tag == "table":
            self.table_stack.append({"has_thead": False, "th_count": 0})
        if tag == "thead" and self.table_stack:
            self.table_stack[-1]["has_thead"] = True
        if tag == "th" and self.table_stack:
            self.table_stack[-1]["th_count"] += 1
        if tag == "label":
            self.label_depth += 1
            if a.get("for"):
                self.labels_for.add(a["for"])

        if tag in {"input", "select", "textarea"}:
            control_id = a.get("id", "")
            explicit = bool(a.get("aria-label") or a.get("aria-labelledby"))
            in_label = self.label_depth > 0
            self.controls.append({
                "tag": tag,
                "id": control_id,
                "in_label": in_label,
                "explicit": explicit,
            })

    def handle_endtag(self, tag):
        if tag == "table" and self.table_stack:
            self.tables.append(self.table_stack.pop())
        if tag == "label" and self.label_depth > 0:
            self.label_depth -= 1


def main():
    errors = []
    for path in sorted(SITE.glob("*.html")):
        parser = A11yParser()
        parser.feed(path.read_text(encoding="utf-8"))

        if not parser.has_lang:
            errors.append(f"{path.relative_to(ROOT)} missing <html lang>")
        if parser.h1_count != 1:
            errors.append(f"{path.relative_to(ROOT)} has {parser.h1_count} h1 tags")
        for idx, t in enumerate(parser.tables, start=1):
            if not t["has_thead"]:
                errors.append(f"{path.relative_to(ROOT)} table #{idx} missing <thead>")
            if t["th_count"] == 0:
                errors.append(f"{path.relative_to(ROOT)} table #{idx} missing <th>")
        for c in parser.controls:
            labeled = c["explicit"] or c["in_label"] or (c["id"] and c["id"] in parser.labels_for)
            if not labeled:
                errors.append(f"{path.relative_to(ROOT)} unlabeled {c['tag']} id='{c['id']}'")

    if errors:
        print("Accessibility checks failed:")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)

    print("Accessibility checks passed for generated pages.")


if __name__ == "__main__":
    main()
