"""Tests for SiteBuilder framework."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_builder import SiteBuilder


@pytest.fixture
def tmp_builder(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "test.html").write_text("Hello {{ name }}!")
    return SiteBuilder(template_dir=template_dir)


def test_register_page(tmp_builder):
    tmp_builder.register(
        "test", "test.html", lambda: {"name": "World", "output_filename": "test.html"}
    )
    assert "test" in tmp_builder.registered_pages


def test_render_page(tmp_builder, tmp_path):
    import builders.config as config
    import site_builder as sb_module

    original_config_site = config.SITE
    original_sb_site = sb_module.SITE
    new_site = tmp_path / "site"
    new_site.mkdir()
    config.SITE = new_site
    sb_module.SITE = new_site
    try:
        tmp_builder.register(
            "test",
            "test.html",
            lambda: {"name": "World", "output_filename": "test.html"},
        )
        tmp_builder.render_page("test")
        output = (new_site / "test.html").read_text()
        assert "Hello World!" == output
    finally:
        config.SITE = original_config_site
        sb_module.SITE = original_sb_site
