from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from vast_dock.models import (
    ApproachRates,
    Limits,
    Port,
    Scenario,
    SoftCaptureChecklist,
    StationState,
    TimelineNode,
    Vehicle,
    Visit,
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROFILES_ROOT = PACKAGE_ROOT / "profiles"


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _resolve(path: Path, base: Path) -> Path:
    if path.is_absolute():
        return path
    candidate = base / path
    if candidate.exists():
        return candidate
    repo_candidate = PACKAGE_ROOT / path
    if repo_candidate.exists():
        return repo_candidate
    return candidate


def load_limits(path: Path | None = None) -> Limits:
    limits_path = path or PROFILES_ROOT / "limits" / "idss-approach-bounds.yaml"
    data = _load_yaml(limits_path)
    approach = data.get("approach", {})
    capture = data.get("capture", {})
    umbilical = data.get("power_umbilical", {})
    return Limits(
        max_axial_rate_m_s=float(approach.get("max_axial_rate_m_s", 0.05)),
        max_lateral_rate_m_s=float(approach.get("max_lateral_rate_m_s", 0.02)),
        max_roll_rate_deg_s=float(approach.get("max_roll_rate_deg_s", 0.3)),
        max_cg_offset_m=float(capture.get("max_cg_offset_m", 0.5)),
        max_vehicle_mass_kg=float(capture.get("max_vehicle_mass_kg", 40000)),
        required_umbilical=list(umbilical.get("required_connectors", ["power", "data", "comms"])),
        synthetic=bool(data.get("synthetic", True)),
    )


def load_vehicle(path: Path) -> Vehicle:
    data = _load_yaml(path)
    approach = data.get("approach", {})
    soft = data.get("soft_capture", {})
    return Vehicle(
        id=data["id"],
        port_standard=data["port_standard"],
        lda_generation=data.get("lda_generation"),
        mass_kg=float(data["mass_kg"]),
        cg_offset_m=float(data["cg_offset_m"]),
        min_opening_m=float(data["min_opening_m"]),
        approach=ApproachRates(
            axial_m_s=float(approach.get("axial_m_s", 0.03)),
            lateral_m_s=float(approach.get("lateral_m_s", 0.01)),
            roll_deg_s=float(approach.get("roll_deg_s", 0.1)),
        ),
        umbilical_connectors=list(data.get("umbilical_connectors", ["power", "data", "comms"])),
        soft_capture=SoftCaptureChecklist(
            retroreflectors=bool(soft.get("retroreflectors", True)),
            latches=bool(soft.get("latches", True)),
            petals=bool(soft.get("petals", True)),
            passive_actuators=bool(soft.get("passive_actuators", True)),
        ),
        hard_capture_bolt_count=int(data.get("hard_capture_bolt_count", 12)),
        synthetic=bool(data.get("synthetic", True)),
    )


def load_station_state(path: Path) -> StationState:
    data = _load_yaml(path)
    ports = [
        Port(
            id=p["id"],
            standard=p["standard"],
            lda_generation=p.get("lda_generation"),
            opening_diameter_m=float(p["opening_diameter_m"]),
            role=p.get("role", "androgynous"),
            compatible_standards=list(p.get("compatible_standards", [p["standard"]])),
            hard_capture_bolt_count=int(p.get("hard_capture_bolt_count", 12)),
        )
        for p in data.get("ports", [])
    ]
    online = data.get("online_date")
    return StationState(
        id=data["id"],
        modules=int(data["modules"]),
        nasa_certified=bool(data.get("nasa_certified", False)),
        consumable_crew_days=int(data.get("consumable_crew_days", 160)),
        ports=ports,
        online_date=_parse_date(online) if online else None,
    )


def load_scenario(path: Path) -> Scenario:
    base = path.parent
    data = _load_yaml(path)
    limits_ref = data.get("limits")
    limits = load_limits(_resolve(Path(limits_ref), base)) if limits_ref else load_limits()

    station_states: dict[str, StationState] = {}
    for state_id, state_ref in (data.get("station_states") or {}).items():
        state_path = _resolve(Path(state_ref), base)
        station_states[state_id] = load_station_state(state_path)

    vehicles: dict[str, Vehicle] = {}
    for vehicle_id, vehicle_ref in (data.get("vehicles") or {}).items():
        vehicle_path = _resolve(Path(vehicle_ref), base)
        vehicle = load_vehicle(vehicle_path)
        vehicles[vehicle_id] = vehicle

    timeline = [
        TimelineNode(
            node_date=_parse_date(node["date"]),
            station_state_id=node["station_state"],
            modules=int(node["modules"]),
        )
        for node in data.get("timeline", [])
    ]

    visits = [
        Visit(
            id=v["id"],
            visit_date=_parse_date(v["date"]),
            vehicle_id=v["vehicle"],
            port_id=v["port"],
            duration_days=int(v["duration_days"]),
            requires_nasa_cert=bool(v.get("requires_nasa_cert", False)),
        )
        for v in data.get("visits", [])
    ]

    return Scenario(
        id=data["scenario"],
        description=str(data.get("description", "")).strip(),
        timeline=timeline,
        visits=visits,
        station_states=station_states,
        vehicles=vehicles,
        limits=limits,
        assumptions=list(data.get("assumptions", [])),
    )


def scenario_hash(scenario: Scenario) -> str:
    payload = {
        "id": scenario.id,
        "timeline": [(n.node_date.isoformat(), n.station_state_id, n.modules) for n in scenario.timeline],
        "visits": [
            (v.id, v.visit_date.isoformat(), v.vehicle_id, v.port_id, v.duration_days)
            for v in scenario.visits
        ],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return digest[:16]
