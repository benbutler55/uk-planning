#!/usr/bin/env python3
import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def page(title: str, subhead: str, active: str, body: str) -> str:
    links = [
        ("index.html", "Overview", "index"),
        ("legislation.html", "Legislation", "legislation"),
        ("plans.html", "Plans", "plans"),
        ("contradictions.html", "Contradictions", "contradictions"),
        ("recommendations.html", "Recommendations", "recommendations"),
        ("methodology.html", "Methodology", "methodology"),
        ("sources.html", "Sources", "sources"),
    ]
    nav = "\n".join(
        f'<a{" class=\"active\"" if key == active else ""} href="{href}">{label}</a>'
        for href, label, key in links
    )
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>{html.escape(title)}</title>
    <link rel=\"stylesheet\" href=\"assets/styles.css\" />
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
    <link href=\"https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap\" rel=\"stylesheet\" />
  </head>
  <body>
    <div class=\"layout\">
      <header>
        <h1>{html.escape(title)}</h1>
        <p class=\"subhead\">{html.escape(subhead)}</p>
      </header>
      <nav>
{nav}
      </nav>
{body}
    </div>
  </body>
</html>
"""


def write(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def render_table(rows, columns):
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(row.get(key, ''))}</td>" for key, _ in columns)
        body.append(f"<tr>{cells}</tr>")
    return (
        "<section class=\"card\"><table><thead><tr>"
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></section>"
    )


def build_index():
    body = """
      <section class=\"card\">
        <h2>Current Phase</h2>
        <p>MVP build initialized. Research ingestion started for England core legislation and national policy corpus.</p>
      </section>
      <section class=\"grid\">
        <article class=\"card\">
          <h3>Goal</h3>
          <p>Build a coherent cross-level planning framework that is faster, clearer, and more predictable.</p>
        </article>
        <article class=\"card\">
          <h3>Outputs</h3>
          <ul>
            <li>Legal and policy inventory</li>
            <li>Plan hierarchy mapping</li>
            <li>Contradiction register</li>
            <li>Actionable reform package</li>
          </ul>
        </article>
        <article class=\"card\">
          <h3>Delivery Horizon</h3>
          <p>6-8 week MVP for policy-professional audience. Static website deployable on GitHub Pages.</p>
        </article>
      </section>
"""
    write(
        SITE / "index.html",
        page(
            "UK Planning System Analysis (England MVP)",
            "Citation-backed analysis of legislation, policy, and local plan layers with reform proposals.",
            "index",
            body,
        ),
    )


def build_legislation():
    rows = read_csv(ROOT / "data/legislation/england-core-legislation.csv")
    columns = [
        ("title", "Instrument"),
        ("type", "Type"),
        ("status", "Status"),
        ("decision_weight", "Decision Weight"),
        ("citation", "Citation"),
    ]
    body = render_table(rows, columns)
    body += "\n<section class=\"card\"><p class=\"small\">Source: <code>data/legislation/england-core-legislation.csv</code></p></section>"
    write(
        SITE / "legislation.html",
        page(
            "Legislation and Regulations Library",
            "England-first inventory of acts and key regulations.",
            "legislation",
            body,
        ),
    )


def build_plans():
    rows = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    columns = [
        ("lpa_name", "Authority"),
        ("lpa_type", "Type"),
        ("region", "Region"),
        ("growth_context", "Growth Context"),
        ("constraint_profile", "Constraints"),
    ]
    body = """
      <section class=\"card\">
        <ul>
          <li>National: NPPF, PPG, relevant NPS</li>
          <li>Regional/sub-regional strategic layers</li>
          <li>County minerals and waste plans</li>
          <li>District/unitary local plans</li>
          <li>Neighbourhood plans</li>
          <li>Sector overlays: flood, heritage, transport, utilities</li>
        </ul>
      </section>
"""
    body += render_table(rows, columns)
    write(
        SITE / "plans.html",
        page(
            "Plan Hierarchy Explorer",
            "Mapped planning stack from national policy to neighbourhood plans and overlays.",
            "plans",
            body,
        ),
    )


def build_contradictions():
    rows = read_csv(ROOT / "data/issues/contradiction-register.csv")
    columns = [
        ("issue_id", "Issue"),
        ("issue_type", "Type"),
        ("affected_pathway", "Pathway"),
        ("severity_score", "Severity"),
        ("delay_impact_score", "Delay Impact"),
        ("summary", "Summary"),
    ]
    body = """
      <section class=\"card\">
        <h2>Scoring Dimensions</h2>
        <ul>
          <li>Severity</li>
          <li>Frequency</li>
          <li>Legal risk</li>
          <li>Delay impact</li>
          <li>Fixability</li>
        </ul>
      </section>
"""
    body += render_table(rows, columns)
    write(
        SITE / "contradictions.html",
        page(
            "Contradictions and Bottlenecks",
            "Cross-layer conflicts and process delay drivers with comparable scoring.",
            "contradictions",
            body,
        ),
    )


def build_recommendations():
    rows = read_csv(ROOT / "data/issues/recommendations.csv")
    columns = [
        ("recommendation_id", "ID"),
        ("title", "Recommendation"),
        ("time_horizon", "Horizon"),
        ("implementation_vehicle", "Vehicle"),
        ("kpi_primary", "Primary KPI"),
        ("target", "Target"),
    ]
    body = render_table(rows, columns)
    write(
        SITE / "recommendations.html",
        page(
            "Recommendations and Model Text",
            "Actionable reforms aligned to legal vehicles, implementation owners, and KPIs.",
            "recommendations",
            body,
        ),
    )


def build_methodology():
    body = """
      <section class=\"card\">
        <h2>Evidence Standard</h2>
        <p>Every substantive finding is linked to citation-backed sources and measurable indicators.</p>
      </section>
      <section class=\"card\">
        <h2>Data Model</h2>
        <p>Core fields include legal status, decision weight, supersession chain, and conflict linkage.</p>
      </section>
"""
    write(
        SITE / "methodology.html",
        page("Methodology", "Taxonomy, source standards, scoring model, and QA controls.", "methodology", body),
    )


def build_sources():
    body = """
      <section class=\"card\">
        <p>Primary source indexes are maintained in <code>content/sources/source-index.md</code>.</p>
      </section>
"""
    write(
        SITE / "sources.html",
        page("Sources and Citations", "Primary legal texts, policy documents, and local plan sources.", "sources", body),
    )


def main():
    build_index()
    build_legislation()
    build_plans()
    build_contradictions()
    build_recommendations()
    build_methodology()
    build_sources()
    print("Built site pages from CSV data.")


if __name__ == "__main__":
    main()
