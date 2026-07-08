from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vast_dock.doctor import evaluate_pairing
from vast_dock.loader import load_scenario
from vast_dock.models import Verdict
from vast_dock.receipt import build_plan, render_markdown, write_receipt
from vast_dock.simulator import run_scenario

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = PACKAGE_ROOT / "out" / "receipts"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vast-dock",
        description="Station Docking Compatibility Workbench — plan, run, doctor, report.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plan_p = sub.add_parser("plan", help="Validate scenario and emit plan manifest")
    plan_p.add_argument("scenario", type=Path, help="Scenario YAML path")
    plan_p.add_argument("--json", action="store_true", help="Emit JSON to stdout")

    run_p = sub.add_parser("run", help="Simulate docking timeline and write receipt")
    run_p.add_argument("scenario", type=Path, help="Scenario YAML path")
    run_p.add_argument("--seed", type=int, default=42, help="Deterministic seed")
    run_p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Receipt output directory")
    run_p.add_argument("--json", action="store_true", help="Print summary JSON to stdout")

    doctor_p = sub.add_parser("doctor", help="Evaluate one vehicle/port pairing or full scenario")
    doctor_p.add_argument("scenario", type=Path, nargs="?", help="Scenario YAML (full timeline doctor)")
    doctor_p.add_argument("--vehicle", type=str, help="Vehicle profile id")
    doctor_p.add_argument("--port", type=str, help="Port id on station state")
    doctor_p.add_argument("--station-state", type=str, help="Station state id for pairing doctor")
    doctor_p.add_argument("--json", action="store_true", help="Emit JSON")

    report_p = sub.add_parser("report", help="Render markdown report from a summary JSON file")
    report_p.add_argument("summary", type=Path, nargs="?", help="Path to summary.json")
    report_p.add_argument("--json", action="store_true", help="Pass through summary JSON")

    args = parser.parse_args(argv)

    if args.command == "plan":
        return _cmd_plan(args)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "doctor":
        return _cmd_doctor(args)
    if args.command == "report":
        return _cmd_report(args)
    return 1


def _cmd_plan(args: argparse.Namespace) -> int:
    scenario = load_scenario(args.scenario)
    manifest = build_plan(scenario)
    payload = manifest.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Scenario: {manifest.scenario_id}")
        print(f"Hash: {manifest.scenario_hash}")
        print(f"Visits: {manifest.visit_count} · Timeline nodes: {manifest.timeline_nodes}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    scenario = load_scenario(args.scenario)
    summary = run_scenario(scenario, seed=args.seed)
    run_dir = write_receipt(summary, args.out)
    if args.json:
        print(json.dumps(summary.as_dict(), indent=2))
    else:
        print(f"Run {summary.run_id} → {run_dir}")
        print(f"Overall verdict: {summary.overall_verdict.value}")
    return 0 if summary.overall_verdict != Verdict.NO_GO else 2


def _cmd_doctor(args: argparse.Namespace) -> int:
    if args.scenario and not (args.vehicle and args.port):
        scenario = load_scenario(args.scenario)
        summary = run_scenario(scenario)
        payload = summary.as_dict()
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Overall: {summary.overall_verdict.value}")
            for visit in summary.visit_results:
                print(f"  {visit.visit_id}: {visit.verdict.value} — {visit.blocking_reasons}")
        return 0 if summary.overall_verdict != Verdict.NO_GO else 2

    if not args.scenario or not args.vehicle or not args.port or not args.station_state:
        print("Pairing doctor requires --scenario, --vehicle, --port, --station-state", file=sys.stderr)
        return 1

    scenario = load_scenario(args.scenario)
    vehicle = scenario.vehicles[args.vehicle]
    station = scenario.station_states[args.station_state]
    port = next((p for p in station.ports if p.id == args.port), None)
    if port is None:
        print(f"Port not found: {args.port}", file=sys.stderr)
        return 1

    findings, checks = evaluate_pairing(vehicle, port, scenario.limits)
    payload = {
        "vehicle": args.vehicle,
        "port": args.port,
        "station_state": args.station_state,
        "checks": checks.as_dict(),
        "findings": [
            {"rule_id": f.rule_id, "severity": f.severity.value, "message": f.message}
            for f in findings
        ],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for finding in findings:
            print(f"{finding.rule_id}: {finding.message}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    summary_path = args.summary or DEFAULT_OUT / "latest" / "summary.json"
    if not summary_path.exists():
        print(f"Summary not found: {summary_path}", file=sys.stderr)
        return 1

    data = json.loads(summary_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(data, indent=2))
        return 0

    from vast_dock.models import DoctorFinding, RunSummary, Severity, Verdict, VisitChecks, VisitResult

    visits = []
    for row in data["visit_results"]:
        findings = [
            DoctorFinding(rule_id=f["rule_id"], severity=Severity(f["severity"]), message=f["message"])
            for f in row.get("findings", [])
        ]
        checks = VisitChecks(**row["checks"])
        visits.append(
            VisitResult(
                visit_id=row["visit_id"],
                visit_date=row["visit_date"],
                station_state=row["station_state"],
                port=row["port"],
                vehicle=row["vehicle"],
                checks=checks,
                findings=findings,
                verdict=Verdict(row["verdict"]),
                blocking_reasons=row.get("blocking_reasons", []),
            )
        )
    summary = RunSummary(
        run_id=data["run_id"],
        scenario_id=data["scenario_id"],
        seed=data["seed"],
        overall_verdict=Verdict(data["overall_verdict"]),
        visit_results=visits,
        assumptions=data.get("assumptions", []),
    )
    print(render_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
