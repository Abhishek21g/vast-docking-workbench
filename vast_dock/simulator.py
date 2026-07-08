from __future__ import annotations

from datetime import datetime, timezone

from vast_dock.doctor import detect_port_conflicts, evaluate_pairing, findings_to_verdict
from vast_dock.models import (
    RunSummary,
    Scenario,
    StationState,
    Verdict,
    VisitResult,
)


def _station_for_date(scenario: Scenario, visit_date) -> tuple[StationState | None, str, bool, bool]:
    """Resolve station state, timeline ok, and module count ok for a visit date."""
    applicable = [node for node in scenario.timeline if node.node_date <= visit_date]
    if not applicable:
        return None, "", False, False

    node = max(applicable, key=lambda n: n.node_date)
    station = scenario.station_states.get(node.station_state_id)
    if station is None:
        return None, node.station_state_id, False, False

    timeline_ok = station.online_date is None or visit_date >= station.online_date
    module_count_ok = station.modules >= node.modules
    return station, node.station_state_id, timeline_ok, module_count_ok


def _consumable_ok(station: StationState, duration_days: int) -> bool:
    return duration_days <= station.consumable_crew_days


def run_scenario(scenario: Scenario, seed: int = 42) -> RunSummary:
    conflict_ids = detect_port_conflicts(scenario.visits)
    visit_results: list[VisitResult] = []

    for visit in sorted(scenario.visits, key=lambda v: v.visit_date):
        vehicle = scenario.vehicles[visit.vehicle_id]
        station, state_id, timeline_ok, module_count_ok = _station_for_date(scenario, visit.visit_date)

        if station is None:
            findings, checks = evaluate_pairing(
                vehicle,
                _placeholder_port(visit.port_id),
                scenario.limits,
                port_available=visit.id not in conflict_ids,
                module_count_ok=False,
                timeline_ok=False,
            )
            visit_results.append(
                VisitResult(
                    visit_id=visit.id,
                    visit_date=visit.visit_date.isoformat(),
                    station_state=state_id or "unknown",
                    port=visit.port_id,
                    vehicle=visit.vehicle_id,
                    checks=checks,
                    findings=findings,
                    verdict=Verdict(findings_to_verdict(findings)),
                    blocking_reasons=[f.rule_id for f in findings if f.severity.value == "no-go"],
                )
            )
            continue

        port = _find_port(station, visit.port_id)
        if port is None:
            from vast_dock.models import DoctorFinding, Severity

            findings = [
                DoctorFinding(
                    rule_id="PORT_NOT_FOUND",
                    severity=Severity.NO_GO,
                    message=f"Port '{visit.port_id}' not defined on station state '{state_id}'",
                )
            ]
            checks = evaluate_pairing(
                vehicle, _placeholder_port(visit.port_id), scenario.limits
            )[1]
            visit_results.append(
                VisitResult(
                    visit_id=visit.id,
                    visit_date=visit.visit_date.isoformat(),
                    station_state=state_id,
                    port=visit.port_id,
                    vehicle=visit.vehicle_id,
                    checks=checks,
                    findings=findings,
                    verdict=Verdict.NO_GO,
                    blocking_reasons=["PORT_NOT_FOUND"],
                )
            )
            continue

        nasa_cert_ok = not visit.requires_nasa_cert or station.nasa_certified
        consumable_ok = _consumable_ok(station, visit.duration_days)
        port_available = visit.id not in conflict_ids

        findings, checks = evaluate_pairing(
            vehicle,
            port,
            scenario.limits,
            port_available=port_available,
            module_count_ok=module_count_ok,
            timeline_ok=timeline_ok,
            nasa_cert_ok=nasa_cert_ok,
            consumable_ok=consumable_ok,
        )

        visit_results.append(
            VisitResult(
                visit_id=visit.id,
                visit_date=visit.visit_date.isoformat(),
                station_state=state_id,
                port=visit.port_id,
                vehicle=visit.vehicle_id,
                checks=checks,
                findings=findings,
                verdict=Verdict(findings_to_verdict(findings)),
                blocking_reasons=[f.rule_id for f in findings if f.severity.value == "no-go"],
            )
        )

    overall = _overall_verdict(visit_results)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    return RunSummary(
        run_id=run_id,
        scenario_id=scenario.id,
        seed=seed,
        overall_verdict=overall,
        visit_results=visit_results,
        assumptions=_collect_assumptions(scenario),
    )


def _overall_verdict(results: list[VisitResult]) -> Verdict:
    if any(r.verdict == Verdict.NO_GO for r in results):
        return Verdict.NO_GO
    if any(r.verdict == Verdict.HUMAN_REVIEW for r in results):
        return Verdict.HUMAN_REVIEW
    return Verdict.DOCK_GO


def _collect_assumptions(scenario: Scenario) -> list[str]:
    assumptions = list(scenario.assumptions)
    if scenario.limits.synthetic:
        assumptions.append("IDSS approach/capture bounds are synthetic placeholders until LDA user guide tables are ingested.")
    assumptions.append("Vehicle profiles are synthetic demo shapes, not proprietary OEM data.")
    assumptions.append("Uses published Vast LDA geometry from vastspace.com only.")
    return assumptions


def _find_port(station: StationState, port_id: str):
    for port in station.ports:
        if port.id == port_id:
            return port
    return None


def _placeholder_port(port_id: str):
    from vast_dock.models import Port

    return Port(
        id=port_id,
        standard="unknown",
        lda_generation=None,
        opening_diameter_m=0.0,
        compatible_standards=[],
    )
