from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _money_map(values: dict[str, str]) -> str:
    if not values:
        return "—"
    return " · ".join(f"{escape(currency)} {escape(amount)}" for currency, amount in values.items())


def _rate_map(values: dict[str, str]) -> str:
    if not values:
        return "—"
    return " · ".join(f"{escape(currency)} {escape(rate)}" for currency, rate in values.items())


def render_html(report: dict[str, Any]) -> str:
    decision = report["decision"]
    summary = report["summary"]
    value = decision["value"]

    rows = []
    for finding in report["findings"]:
        rows.append(
            "<tr>"
            f"<td><code>{escape(str(finding['key']))}</code></td>"
            f"<td><strong>{escape(finding['classification'])}</strong></td>"
            f"<td>{escape(finding['confidence'])}</td>"
            f"<td>{escape(str(finding.get('truth_value') or '—'))}</td>"
            f"<td>{escape(str(finding.get('ga4_value') or '—'))}</td>"
            f"<td>{escape(str(finding.get('currency') or '—'))}</td>"
            f"<td>{escape(str(finding.get('reason') or '—'))}</td>"
            "</tr>"
        )

    class_cards = "".join(
        f"<div class='metric'><span>{escape(k)}</span><strong>{v}</strong></div>"
        for k, v in summary.items()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Conversion Truth Report</title>
<style>
:root {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:#171717; background:#f6f7f8; }}
body {{ margin:0; }}
main {{ max-width:1120px; margin:0 auto; padding:48px 24px 80px; }}
.eyebrow {{ font-size:13px; text-transform:uppercase; letter-spacing:.12em; color:#666; }}
h1 {{ font-size:42px; margin:8px 0 10px; }}
.lead {{ font-size:18px; color:#555; margin:0 0 28px; }}
.panel {{ background:white; border:1px solid #dedede; border-radius:14px; padding:24px; margin:18px 0; box-shadow:0 2px 12px rgba(0,0,0,.035); }}
.decision {{ display:flex; gap:24px; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; }}
.badge {{ font-size:28px; font-weight:800; padding:10px 16px; border-radius:10px; background:#f0f0f0; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }}
.metric {{ border:1px solid #e5e5e5; border-radius:10px; padding:14px; }}
.metric span {{ display:block; color:#666; font-size:12px; margin-bottom:6px; }}
.metric strong {{ font-size:24px; }}
.kv {{ display:grid; grid-template-columns:minmax(180px,1fr) 2fr; gap:10px 20px; }}
.kv div:nth-child(odd) {{ color:#666; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th,td {{ text-align:left; padding:11px 9px; border-bottom:1px solid #e8e8e8; vertical-align:top; }}
th {{ color:#555; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
code {{ font-family:ui-monospace, SFMono-Regular, Menlo, monospace; }}
.note {{ color:#666; font-size:13px; }}
</style>
</head>
<body><main>
<div class="eyebrow">Conversion Truth Auditor</div>
<h1>Are your conversion numbers telling the truth?</h1>
<p class="lead">Evidence-backed reconciliation of GA4 purchases against real business outcomes.</p>
<section class="panel decision">
<div>
<div class="eyebrow">Decision</div>
<div class="badge">{escape(decision['decision'])}</div>
</div>
<div class="kv">
<div>Reason</div><div>{escape(decision['reason'])}</div>
<div>Evidence status</div><div>{escape(decision['evidence_status'])}</div>
<div>Confirmed error rate</div><div>{escape(str(decision['confirmed_error_rate']))}</div>
<div>Policy</div><div>Block at ≥ {escape(decision['policy']['block_error_rate'])} confirmed group error rate or ≥ {escape(decision['policy']['block_value_rate'])} discrepancy value vs GA4 reported value.</div>
</div>
</section>
<section class="panel">
<h2>Classification summary</h2>
<div class="grid">{class_cards}</div>
</section>
<section class="panel">
<h2>Value evidence</h2>
<div class="kv">
<div>GA4 reported</div><div>{_money_map(value['ga4_reported'])}</div>
<div>Confirmed overreported</div><div>{_money_map(value['confirmed_overreported'])}</div>
<div>Confirmed underreported</div><div>{_money_map(value['confirmed_underreported'])}</div>
<div>Confirmed discrepancy</div><div>{_money_map(value['confirmed_discrepancy'])}</div>
<div>Unresolved</div><div>{_money_map(value['unresolved'])}</div>
<div>Discrepancy rate</div><div>{_rate_map(value['confirmed_discrepancy_rate_vs_ga4_reported'])}</div>
</div>
<p class="note">These are reconciliation differences, not claims of revenue loss. Currency mismatches are not aggregated without FX evidence.</p>
</section>
<section class="panel">
<h2>Evidence</h2>
<table>
<thead><tr><th>Key</th><th>Class</th><th>Confidence</th><th>Truth</th><th>GA4</th><th>Currency</th><th>Reason</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</section>
</main></body></html>"""


def write_html(report: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(render_html(report), encoding="utf-8")
