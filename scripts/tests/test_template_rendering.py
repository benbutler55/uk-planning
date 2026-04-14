"""Tests for template rendering — verify each template produces valid HTML."""
import sys
from pathlib import Path
from html.parser import HTMLParser

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_builder import SiteBuilder
from builders.data_loader import load_scoring


class StructureChecker(HTMLParser):
    """Minimal HTML structure checker."""
    def __init__(self):
        super().__init__()
        self.has_doctype = False
        self.has_html_lang = False
        self.h1_count = 0
        self.has_main = False
        self.has_title = False
        self._in_title = False
        self.title_text = ""

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype"):
            self.has_doctype = True

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.has_html_lang = True
        if tag == "h1":
            self.h1_count += 1
        if tag == "main":
            self.has_main = True
        if tag == "title":
            self._in_title = True
            self.has_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title_text += data


def check_html_structure(html_content, page_name):
    """Verify basic HTML structure requirements."""
    checker = StructureChecker()
    checker.feed(html_content)
    assert checker.has_html_lang, f"{page_name}: missing <html lang>"
    assert checker.h1_count == 1, f"{page_name}: expected 1 <h1>, found {checker.h1_count}"
    assert checker.has_main, f"{page_name}: missing <main>"
    assert checker.has_title, f"{page_name}: missing <title>"
    assert len(checker.title_text.strip()) > 0, f"{page_name}: empty <title>"


@pytest.fixture(scope="module")
def builder():
    return SiteBuilder()


def render_context(builder, template_path, context_fn):
    """Render a template and return the HTML string."""
    template = builder.env.get_template(template_path)
    ctx = context_fn()
    return template.render(**ctx)


# --- Methods pages ---

def test_render_methodology(builder):
    from builders.context_providers.methods import methodology_context
    html = render_context(builder, "pages/methodology.html", methodology_context)
    check_html_structure(html, "methodology")
    assert "Scoring Model" in html


def test_render_data_health(builder):
    from builders.context_providers.methods import data_health_context
    html = render_context(builder, "pages/data_health.html", data_health_context)
    check_html_structure(html, "data-health")


# --- Overview pages ---

def test_render_index(builder):
    from builders.context_providers.overview import index_context
    html = render_context(builder, "pages/index.html", index_context)
    check_html_structure(html, "index")
    assert "England at a glance" in html


def test_render_search(builder):
    from builders.context_providers.overview import search_context
    html = render_context(builder, "pages/search.html", search_context)
    check_html_structure(html, "search")
    assert "search-input" in html


# --- Audience pages ---

def test_render_audience_public(builder):
    from builders.context_providers.audiences import public_context
    html = render_context(builder, "pages/audience_public.html", public_context)
    check_html_structure(html, "audience-public")
    assert "What Is This Project?" in html


# --- Spot check a detail page ---

def test_render_contradiction_detail(builder):
    from builders.context_providers.analysis import contradiction_detail_contexts
    weights = load_scoring()
    contexts = contradiction_detail_contexts(weights)
    if contexts:
        ctx = contexts[0]
        template = builder.env.get_template("pages/contradiction_detail.html")
        html = template.render(**ctx)
        check_html_structure(html, ctx["output_filename"])
        assert "detail-layout" in html
