from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from vast_dock.doctor import detect_port_conflicts, evaluate_pairing, findings_to_verdict
from vast_dock.loader import load_scenario, load_vehicle, scenario_hash
from vast_dock.models import (
    ApproachRates,
    DoctorFinding,
    Port,
    Severity,
    SoftCaptureChecklist,
    StationState,
    Vehicle,
    Visit,
)
from vast_dock.receipt import build_plan
from vast_dock.simulator import run_scenario

ROOT = Path(__file__).resolve().parent.parent
LIMITS = load_scenario(ROOT / "examples" / "haven2-growth-2028.yaml").limits


def _vehicle(**kwargs) -> Vehicle:
    defaults = dict(
        id="test-vehicle",
        port_standard="lda",
        lda_generation="gen-1",
        mass_kg=10000,
        cg_offset_m=0.3,
        min_opening_m=2.0,
        approach=ApproachRates(0.03, 0.01, 0.1),
    )
    defaults.update(kwargs)
    return Vehicle(**defaults)


def _port(**kwargs) -> Port:
    defaults = dict(
        id="forward-lda",
        standard="lda",
        lda_generation="gen-1",
        opening_diameter_m=2.9,
        compatible_standards=["lda"],
    )
    defaults.update(kwargs)
    return Port(**defaults)


def test_load_haven2_scenario():
    scenario = load_scenario(ROOT / "examples" / "haven2-growth-2028.yaml")
    assert scenario.id == "haven2-growth-2028"
    assert len(scenario.visits) == 3
    assert "crew-dragon-lda-gen1" in scenario.vehicles


def test_scenario_hash_stable():
    scenario = load_scenario(ROOT / "examples" / "haven2-growth-2028.yaml")
    assert scenario_hash(scenario) == scenario_hash(scenario)


def test_plan_manifest_counts():
    scenario = load_scenario(ROOT / "examples" / "haven2-growth-2028.yaml")
    plan = build_plan(scenario)
    assert plan.visit_count == 3
    assert plan.timeline_nodes == 3


def test_compatible_lda_pairing_dock_go():
    findings, _ = evaluate_pairing(_vehicle(), _port(), LIMITS)
    assert findings_to_verdict(findings) == "dock-go"


def test_port_standard_mismatch():
    findings, checks = evaluate_pairing(
        _vehicle(port_standard="cbm"), _port(compatible_standards=["lda"]), LIMITS
    )
    assert not checks.interface_match
    assert any(f.rule_id == "PORT_STANDARD_MISMATCH" for f in findings)


def test_lda_generation_mismatch():
    findings, _ = evaluate_pairing(
        _vehicle(lda_generation="gen-2"), _port(lda_generation="gen-1"), LIMITS
    )
    assert any(f.rule_id == "LDA_GEN_MISMATCH" for f in findings)


def test_opening_undersize():
    findings, checks = evaluate_pairing(
        _vehicle(min_opening_m=3.5), _port(opening_diameter_m=2.9), LIMITS
    )
    assert not checks.opening_clearance
    assert any(f.rule_id == "OPENING_UNDERSIZE" for f in findings)


def test_cg_envelope_exceed():
    findings, checks = evaluate_pairing(_vehicle(cg_offset_m=0.9), _port(), LIMITS)
    assert not checks.capture_envelope
    assert any(f.rule_id == "CG_ENVELOPE_EXCEED" for f in findings)


def test_mass_cap_human_review():
    findings, _ = evaluate_pairing(_vehicle(mass_kg=50000), _port(), LIMITS)
    assert any(f.rule_id == "MASS_CAP_EXCEED" for f in findings)
    assert findings_to_verdict(findings) == "human-review"


def test_approach_rate_exceed():
    findings, checks = evaluate_pairing(
        _vehicle(approach=ApproachRates(0.2, 0.01, 0.1)), _port(), LIMITS
    )
    assert not checks.approach_rates
    assert any(f.rule_id == "APPROACH_RATE_EXCEED" for f in findings)


def test_hard_capture_bolt_mismatch():
    findings, _ = evaluate_pairing(_vehicle(hard_capture_bolt_count=8), _port(), LIMITS)
    assert any(f.rule_id == "HARD_CAPTURE_BOLT_MISMATCH" for f in findings)


def test_soft_capture_incomplete():
    soft = SoftCaptureChecklist(retroreflectors=False)
    findings, _ = evaluate_pairing(_vehicle(soft_capture=soft), _port(), LIMITS)
    assert any(f.rule_id == "SOFT_CAPTURE_INCOMPLETE" for f in findings)


def test_umbilical_missing():
    findings, checks = evaluate_pairing(
        _vehicle(umbilical_connectors=["power"]), _port(), LIMITS
    )
    assert not checks.umbilical_checklist
    assert any(f.rule_id == "UMBILICAL_MISSING" for f in findings)


def test_port_double_booking_flag():
    findings, checks = evaluate_pairing(_vehicle(), _port(), LIMITS, port_available=False)
    assert not checks.port_available
    assert any(f.rule_id == "PORT_DOUBLE_BOOKING" for f in findings)


def test_module_count_underflow():
    findings, _ = evaluate_pairing(_vehicle(), _port(), LIMITS, module_count_ok=False)
    assert any(f.rule_id == "MODULE_COUNT_UNDERFLOW" for f in findings)


def test_timeline_before_module():
    findings, _ = evaluate_pairing(_vehicle(), _port(), LIMITS, timeline_ok=False)
    assert any(f.rule_id == "TIMELINE_BEFORE_MODULE" for f in findings)


def test_nasa_cert_required():
    findings, _ = evaluate_pairing(_vehicle(), _port(), LIMITS, nasa_cert_ok=False)
    assert any(f.rule_id == "NASA_CERT_REQUIRED" for f in findings)


def test_consumable_crew_days():
    findings, _ = evaluate_pairing(_vehicle(), _port(), LIMITS, consumable_ok=False)
    assert any(f.rule_id == "CONSUMABLE_CREW_DAYS" for f in findings)


def test_detect_port_conflicts():
    visits = [
        Visit("a", date(2029, 6, 10), "v", "forward-lda", 14),
        Visit("b", date(2029, 6, 15), "v", "forward-lda", 7),
    ]
    conflicts = detect_port_conflicts(visits)
    assert "a" in conflicts and "b" in conflicts


def test_no_conflict_different_ports():
    visits = [
        Visit("a", date(2029, 6, 10), "v", "forward-lda", 14),
        Visit("b", date(2029, 6, 12), "v", "aft-lda", 14),
    ]
    assert not detect_port_conflicts(visits)


def test_run_haven2_overall_no_go():
    scenario = load_scenario(ROOT / "examples" / "haven2-growth-2028.yaml")
    summary = run_scenario(scenario, seed=42)
    assert summary.overall_verdict.value == "no-go"
    cargo = next(v for v in summary.visit_results if v.visit_id == "cargo-cbm-2029")
    assert "PORT_STANDARD_MISMATCH" in [f.rule_id for f in cargo.findings]
    uk = next(v for v in summary.visit_results if v.visit_id == "uk-crew-2029-a")
    assert "PORT_DOUBLE_BOOKING" in [f.rule_id for f in uk.findings]


def test_run_haven1_dock_go():
    scenario = load_scenario(ROOT / "examples" / "haven1-crew-visit.yaml")
    summary = run_scenario(scenario)
    assert summary.overall_verdict.value == "dock-go"


def test_load_synthetic_vehicle_flag():
    vehicle = load_vehicle(ROOT / "profiles" / "vehicles" / "heavy-visit-synthetic.yaml")
    assert vehicle.synthetic is True
    assert vehicle.mass_kg == 45000


def test_findings_to_verdict_priority():
    assert findings_to_verdict([DoctorFinding("X", Severity.HUMAN_REVIEW, "m")]) == "human-review"
    assert (
        findings_to_verdict(
            [
                DoctorFinding("A", Severity.HUMAN_REVIEW, "m"),
                DoctorFinding("B", Severity.NO_GO, "m"),
            ]
        )
        == "no-go"
    )


def test_station_state_port_count():
    scenario = load_scenario(ROOT / "examples" / "haven2-growth-2028.yaml")
    state = scenario.station_states["haven2-3module"]
    assert len(state.ports) == 2
    assert state.nasa_certified is True
