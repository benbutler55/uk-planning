#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "href" in attrs_dict:
            self.links.append(attrs_dict["href"])
        if tag == "link" and "href" in attrs_dict:
            self.links.append(attrs_dict["href"])
        if tag == "script" and "src" in attrs_dict:
            self.links.append(attrs_dict["src"])


def is_external(link):
    return (
        link.startswith("http://")
        or link.startswith("https://")
        or link.startswith("mailto:")
    )


def normalize(link):
    if "#" in link:
        return link.split("#", 1)[0]
    return link


def main():
    errors = []
    html_files = sorted(SITE.glob("*.html"))
    for html_file in html_files:
        collector = LinkCollector()
        collector.feed(html_file.read_text(encoding="utf-8"))
        for link in collector.links:
            if not link or is_external(link):
                continue
            local_link = normalize(link)
            if not local_link:
                continue
            target = (html_file.parent / local_link).resolve()
            if not target.exists():
                errors.append(f"{html_file.relative_to(ROOT)} -> missing {local_link}")

    if errors:
        print("Link check failed:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)

    print("Link check passed for generated site HTML.")


if __name__ == "__main__":
    main()
