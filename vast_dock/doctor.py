from __future__ import annotations

from vast_dock.models import (
    DoctorFinding,
    Limits,
    Port,
    Severity,
    SoftCaptureChecklist,
    StationState,
    Vehicle,
    Visit,
    VisitChecks,
)


def _port_by_id(station: StationState, port_id: str) -> Port | None:
    for port in station.ports:
        if port.id == port_id:
            return port
    return None


def evaluate_pairing(
    vehicle: Vehicle,
    port: Port,
    limits: Limits,
    *,
    port_available: bool = True,
    module_count_ok: bool = True,
    timeline_ok: bool = True,
    nasa_cert_ok: bool = True,
    consumable_ok: bool = True,
) -> tuple[list[DoctorFinding], VisitChecks]:
    findings: list[DoctorFinding] = []

    interface_match = vehicle.port_standard in port.compatible_standards
    if not interface_match:
        findings.append(
            DoctorFinding(
                rule_id="PORT_STANDARD_MISMATCH",
                severity=Severity.NO_GO,
                message=(
                    f"Vehicle standard '{vehicle.port_standard}' not in port "
                    f"compatible set {port.compatible_standards}"
                ),
            )
        )

    if vehicle.lda_generation and port.lda_generation and vehicle.lda_generation != port.lda_generation:
        findings.append(
            DoctorFinding(
                rule_id="LDA_GEN_MISMATCH",
                severity=Severity.NO_GO,
                message=(
                    f"LDA generation mismatch: vehicle {vehicle.lda_generation} "
                    f"vs port {port.lda_generation}"
                ),
            )
        )

    opening_clearance = vehicle.min_opening_m <= port.opening_diameter_m
    if not opening_clearance:
        findings.append(
            DoctorFinding(
                rule_id="OPENING_UNDERSIZE",
                severity=Severity.NO_GO,
                message=(
                    f"Vehicle needs {vehicle.min_opening_m} m opening; port provides "
                    f"{port.opening_diameter_m} m"
                ),
            )
        )

    approach_rates = (
        vehicle.approach.axial_m_s <= limits.max_axial_rate_m_s
        and vehicle.approach.lateral_m_s <= limits.max_lateral_rate_m_s
        and vehicle.approach.roll_deg_s <= limits.max_roll_rate_deg_s
    )
    if not approach_rates:
        findings.append(
            DoctorFinding(
                rule_id="APPROACH_RATE_EXCEED",
                severity=Severity.NO_GO,
                message="Vehicle approach rates exceed IDSS-class bounds (synthetic)",
            )
        )

    capture_envelope = vehicle.cg_offset_m <= limits.max_cg_offset_m
    if not capture_envelope:
        findings.append(
            DoctorFinding(
                rule_id="CG_ENVELOPE_EXCEED",
                severity=Severity.NO_GO,
                message=(
                    f"CG offset {vehicle.cg_offset_m} m exceeds capture envelope "
                    f"{limits.max_cg_offset_m} m"
                ),
            )
        )

    if vehicle.mass_kg > limits.max_vehicle_mass_kg:
        findings.append(
            DoctorFinding(
                rule_id="MASS_CAP_EXCEED",
                severity=Severity.HUMAN_REVIEW,
                message=(
                    f"Vehicle mass {vehicle.mass_kg} kg exceeds soft cap "
                    f"{limits.max_vehicle_mass_kg} kg"
                ),
            )
        )

    if vehicle.hard_capture_bolt_count != port.hard_capture_bolt_count:
        findings.append(
            DoctorFinding(
                rule_id="HARD_CAPTURE_BOLT_MISMATCH",
                severity=Severity.NO_GO,
                message=(
                    f"Bolt count mismatch: vehicle {vehicle.hard_capture_bolt_count} "
                    f"vs port {port.hard_capture_bolt_count}"
                ),
            )
        )

    soft_ok = _soft_capture_complete(vehicle.soft_capture)
    if not soft_ok:
        findings.append(
            DoctorFinding(
                rule_id="SOFT_CAPTURE_INCOMPLETE",
                severity=Severity.HUMAN_REVIEW,
                message="Soft-capture checklist incomplete on vehicle profile",
            )
        )

    umbilical_ok = all(conn in vehicle.umbilical_connectors for conn in limits.required_umbilical)
    if not umbilical_ok:
        findings.append(
            DoctorFinding(
                rule_id="UMBILICAL_MISSING",
                severity=Severity.HUMAN_REVIEW,
                message=(
                    f"Missing umbilical connectors; required {limits.required_umbilical}, "
                    f"vehicle has {vehicle.umbilical_connectors}"
                ),
            )
        )

    if not module_count_ok:
        findings.append(
            DoctorFinding(
                rule_id="MODULE_COUNT_UNDERFLOW",
                severity=Severity.NO_GO,
                message="Station module count below scenario requirement for this visit",
            )
        )

    if not timeline_ok:
        findings.append(
            DoctorFinding(
                rule_id="TIMELINE_BEFORE_MODULE",
                severity=Severity.NO_GO,
                message="Visit occurs before required station state is online",
            )
        )

    if not nasa_cert_ok:
        findings.append(
            DoctorFinding(
                rule_id="NASA_CERT_REQUIRED",
                severity=Severity.HUMAN_REVIEW,
                message="Visit requires NASA certification but station is not certified",
            )
        )

    if not consumable_ok:
        findings.append(
            DoctorFinding(
                rule_id="CONSUMABLE_CREW_DAYS",
                severity=Severity.HUMAN_REVIEW,
                message="Visit duration exceeds remaining consumable crew-days budget",
            )
        )

    if not port_available:
        findings.append(
            DoctorFinding(
                rule_id="PORT_DOUBLE_BOOKING",
                severity=Severity.NO_GO,
                message="Port already booked by overlapping visit",
            )
        )

    checks = VisitChecks(
        interface_match=interface_match,
        opening_clearance=opening_clearance,
        approach_rates=approach_rates,
        capture_envelope=capture_envelope,
        umbilical_checklist=umbilical_ok,
        port_available=port_available,
        module_count_ok=module_count_ok,
        timeline_ok=timeline_ok,
        nasa_cert_ok=nasa_cert_ok,
        consumable_ok=consumable_ok,
    )
    return findings, checks


def _soft_capture_complete(soft: SoftCaptureChecklist) -> bool:
    return soft.retroreflectors and soft.latches and soft.petals and soft.passive_actuators


def detect_port_conflicts(visits: list[Visit]) -> set[tuple[str, str]]:
    """Return visit ids that conflict on (port_id, overlapping window)."""
    conflicts: set[str] = set()
    ordered = sorted(visits, key=lambda v: (v.port_id, v.visit_date))
    for i, left in enumerate(ordered):
        left_end = left.visit_date.toordinal() + left.duration_days
        for right in ordered[i + 1 :]:
            if right.port_id != left.port_id:
                continue
            if right.visit_date.toordinal() < left_end:
                conflicts.add(left.id)
                conflicts.add(right.id)
            else:
                break
    return conflicts


def findings_to_verdict(findings: list[DoctorFinding]) -> str:
    if any(f.severity == Severity.NO_GO for f in findings):
        return "no-go"
    if any(f.severity == Severity.HUMAN_REVIEW for f in findings):
        return "human-review"
    return "dock-go"
