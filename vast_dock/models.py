from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    DOCK_GO = "dock-go"
    HUMAN_REVIEW = "human-review"
    NO_GO = "no-go"


class Severity(str, Enum):
    NO_GO = "no-go"
    HUMAN_REVIEW = "human-review"


@dataclass
class ApproachRates:
    axial_m_s: float
    lateral_m_s: float
    roll_deg_s: float


@dataclass
class SoftCaptureChecklist:
    retroreflectors: bool = True
    latches: bool = True
    petals: bool = True
    passive_actuators: bool = True


@dataclass
class Port:
    id: str
    standard: str
    lda_generation: str | None
    opening_diameter_m: float
    role: str = "androgynous"
    compatible_standards: list[str] = field(default_factory=list)
    hard_capture_bolt_count: int = 12

    def __post_init__(self) -> None:
        if not self.compatible_standards:
            self.compatible_standards = [self.standard]


@dataclass
class StationState:
    id: str
    modules: int
    nasa_certified: bool
    consumable_crew_days: int
    ports: list[Port]
    online_date: date | None = None


@dataclass
class Vehicle:
    id: str
    port_standard: str
    lda_generation: str | None
    mass_kg: float
    cg_offset_m: float
    min_opening_m: float
    approach: ApproachRates
    umbilical_connectors: list[str] = field(default_factory=list)
    soft_capture: SoftCaptureChecklist = field(default_factory=SoftCaptureChecklist)
    hard_capture_bolt_count: int = 12
    synthetic: bool = True

    def __post_init__(self) -> None:
        if not self.umbilical_connectors:
            self.umbilical_connectors = ["power", "data", "comms"]


@dataclass
class Visit:
    id: str
    visit_date: date
    vehicle_id: str
    port_id: str
    duration_days: int
    requires_nasa_cert: bool = False


@dataclass
class TimelineNode:
    node_date: date
    station_state_id: str
    modules: int


@dataclass
class Limits:
    max_axial_rate_m_s: float
    max_lateral_rate_m_s: float
    max_roll_rate_deg_s: float
    max_cg_offset_m: float
    max_vehicle_mass_kg: float
    required_umbilical: list[str]
    synthetic: bool = True


@dataclass
class Scenario:
    id: str
    description: str
    timeline: list[TimelineNode]
    visits: list[Visit]
    station_states: dict[str, StationState]
    vehicles: dict[str, Vehicle]
    limits: Limits
    assumptions: list[str] = field(default_factory=list)


@dataclass
class DoctorFinding:
    rule_id: str
    severity: Severity
    message: str


@dataclass
class VisitChecks:
    interface_match: bool
    opening_clearance: bool
    approach_rates: bool
    capture_envelope: bool
    umbilical_checklist: bool
    port_available: bool
    module_count_ok: bool
    timeline_ok: bool
    nasa_cert_ok: bool
    consumable_ok: bool

    def as_dict(self) -> dict[str, bool]:
        return {
            "interface_match": self.interface_match,
            "opening_clearance": self.opening_clearance,
            "approach_rates": self.approach_rates,
            "capture_envelope": self.capture_envelope,
            "umbilical_checklist": self.umbilical_checklist,
            "port_available": self.port_available,
            "module_count_ok": self.module_count_ok,
            "timeline_ok": self.timeline_ok,
            "nasa_cert_ok": self.nasa_cert_ok,
            "consumable_ok": self.consumable_ok,
        }


@dataclass
class VisitResult:
    visit_id: str
    visit_date: str
    station_state: str
    port: str
    vehicle: str
    checks: VisitChecks
    findings: list[DoctorFinding]
    verdict: Verdict
    blocking_reasons: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "visit_id": self.visit_id,
            "visit_date": self.visit_date,
            "station_state": self.station_state,
            "port": self.port,
            "vehicle": self.vehicle,
            "checks": self.checks.as_dict(),
            "findings": [
                {"rule_id": f.rule_id, "severity": f.severity.value, "message": f.message}
                for f in self.findings
            ],
            "verdict": self.verdict.value,
            "blocking_reasons": self.blocking_reasons,
        }


@dataclass
class PlanManifest:
    scenario_id: str
    description: str
    scenario_hash: str
    visit_count: int
    timeline_nodes: int
    assumptions: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "description": self.description,
            "scenario_hash": self.scenario_hash,
            "visit_count": self.visit_count,
            "timeline_nodes": self.timeline_nodes,
            "assumptions": self.assumptions,
        }


@dataclass
class RunSummary:
    run_id: str
    scenario_id: str
    seed: int
    overall_verdict: Verdict
    visit_results: list[VisitResult]
    assumptions: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "overall_verdict": self.overall_verdict.value,
            "visit_results": [v.as_dict() for v in self.visit_results],
            "assumptions": self.assumptions,
        }
