"""SiteBuilder: Jinja2-based static site generator for uk-planning."""

import sys
from pathlib import Path

import jinja2

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders.config import SITE
from builders.html_helpers import register_helpers


class SiteBuilder:
    def __init__(self, template_dir=None):
        if template_dir is None:
            template_dir = Path(__file__).resolve().parent / "templates"
        self.template_dir = template_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        register_helpers(self.env)
        self._pages = {}

    def register(self, page_name, template_path, context_fn):
        """Register a page: name, template file path, and a callable returning a context dict."""
        self._pages[page_name] = (template_path, context_fn)

    def render_page(self, page_name):
        """Render a single registered page and write to site/."""
        template_path, context_fn = self._pages[page_name]
        template = self.env.get_template(template_path)
        context = context_fn()
        html = template.render(**context)
        out_path = SITE / context.get("output_filename", f"{page_name}.html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")

    def render_all(self):
        """Render all registered pages."""
        for page_name in self._pages:
            self.render_page(page_name)

    @property
    def registered_pages(self):
        return set(self._pages.keys())
