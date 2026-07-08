from __future__ import annotations

import json
from pathlib import Path

from vast_dock.loader import scenario_hash
from vast_dock.models import PlanManifest, RunSummary, Scenario


def build_plan(scenario: Scenario) -> PlanManifest:
    return PlanManifest(
        scenario_id=scenario.id,
        description=scenario.description,
        scenario_hash=scenario_hash(scenario),
        visit_count=len(scenario.visits),
        timeline_nodes=len(scenario.timeline),
        assumptions=list(scenario.assumptions),
    )


def write_receipt(summary: RunSummary, out_dir: Path) -> Path:
    run_dir = out_dir / summary.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary.as_dict(), indent=2) + "\n", encoding="utf-8")

    report_path = run_dir / "report.md"
    report_path.write_text(render_markdown(summary), encoding="utf-8")

    latest = out_dir / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "summary.json").write_text(summary_path.read_text(encoding="utf-8"), encoding="utf-8")
    (latest / "report.md").write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")

    return run_dir


def render_markdown(summary: RunSummary) -> str:
    lines = [
        f"# Docking Compatibility Report — {summary.scenario_id}",
        "",
        f"- **Run ID:** `{summary.run_id}`",
        f"- **Seed:** {summary.seed}",
        f"- **Overall verdict:** `{summary.overall_verdict.value}`",
        "",
        "## Visit results",
        "",
    ]
    for visit in summary.visit_results:
        lines.append(f"### {visit.visit_id} — `{visit.verdict.value}`")
        lines.append("")
        lines.append(
            f"- Date: {visit.visit_date} · Station: `{visit.station_state}` · "
            f"Port: `{visit.port}` · Vehicle: `{visit.vehicle}`"
        )
        if visit.blocking_reasons:
            lines.append(f"- Blocking: {', '.join(visit.blocking_reasons)}")
        if visit.findings:
            lines.append("- Findings:")
            for finding in visit.findings:
                lines.append(f"  - **{finding.rule_id}** ({finding.severity.value}): {finding.message}")
        lines.append("")

    lines.extend(["## Assumptions", ""])
    for assumption in summary.assumptions:
        lines.append(f"- {assumption}")
    lines.append("")
    return "\n".join(lines)
