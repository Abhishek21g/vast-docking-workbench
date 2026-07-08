# Vast Space — Target Brief (LDA → Simulator Params)

**Phase 1 only.** No product code until this mapping is reviewed.  
**Constraint:** Public LDA interface user guide + website specs only. Label all stiffness/load numbers as *order-of-magnitude assumptions* unless explicitly published.

---

## 1. Executive problem → simulator scope

Vast's near-term existential bet is **winning CLD** while **bootstrapping an LDA ecosystem** before competitors lock partners into proprietary ports. The expensive failure mode is not a bad weld — it is:

1. A **partner vehicle** discovers late that it cannot berth during a planned visit window.
2. A **module integration** proceeds on paper but violates CG / capture envelope when real mass properties arrive.
3. **Haven-2 growth** books both docking ports while a government mission still needs a crew swap berth.

The MVP simulator is deliberately narrow (docking compatibility) but models the **growth collision** executives care about: *can the attach-point network absorb the traffic we are publicly signing?*

---

## 2. Published LDA geometry → core constants

| Parameter | Published value | Simulator field | Source |
|-----------|-----------------|-----------------|--------|
| Outer diameter | 3.65 m | `lda.outer_diameter_m` | [LDA page](https://www.vastspace.com/large-docking-adapter) |
| Pressurized opening diameter | 2.90 m | `lda.pressurized_opening_diameter_m` | same |
| Pressurized opening area | 6.6 m² | `lda.pressurized_opening_area_m2` | same |
| Module count scale | 2 – 20+ | `station.module_count` (int, ≥2) | LDA page + press release |
| Architecture | Androgynous | `port.role: androgynous` (no fixed active/passive) | press release |
| IDSS heritage | Compatible approach rates & loads | `vehicle.approach.max_rate_m_s`, `vehicle.approach.max_load_kN` (bounded by IDSS table — synthetic YAML) | LDA page |
| Soft capture | 3 retroreflectors, 3 latches, 3 petals, 6 passive actuators | `capture.soft_capture_checklist` (boolean flags in doctor) | LDA page |
| Hard capture | 12 powered bolts, alignment pins, redundant seals | `capture.hard_capture_bolt_count: 12` | LDA page |
| Rigidity claim | ~30× IDA | `adapter.rigidity_factor_vs_ida: 30` (comparison metric only, not absolute N/m) | press release |
| Comparison anchors | IDA 0.8 m, CBM 1.6 m, LDA 2.9 m opening | `port.standard: ida\|cbm\|lda` enum + opening diameter | LDA page |
| LDA generation | gen-1 (interface guide May 2026) | `lda.generation: "gen-1"` | press release + May update |
| Availability | Purchase from Vast OR self-manufacture to guide | N/A (licensing model, not sim param) | press release |

---

## 3. Published station profiles → YAML templates

### Haven-1 (`profiles/stations/haven-1.yaml`)

| Field | Value | Notes |
|-------|-------|-------|
| `station.id` | `haven-1` | |
| `station.launch_vehicle` | `falcon-9` | website |
| `station.mass_dry_kg` | 14600 | website |
| `station.crew_capacity` | 4 | website |
| `station.habitable_volume_m3` | 45 | website |
| `station.pressurized_volume_m3` | 80 | website |
| `station.power_w` | 13200 | website |
| `station.orbit` | `{inc_deg: 51.6, alt_km: 425}` | website |
| `station.ports` | 1 × forward (IDA-class passive per fit-check news; **demo assumes LDA-capable forward port**) | website news: "passive docking hardware fit check" — mark `assumption: lda_forward` in receipt |
| `station.nasa_certified` | false | Haven-2 comparison table |

### Haven-2 module (`profiles/stations/haven-2-module.yaml`)

| Field | Value |
|-------|-------|
| `station.diameter_m` | 4.4 |
| `station.length_m` | 16 |
| `station.mass_dry_kg` | 29000 |
| `station.habitable_volume_m3` | 55 |
| `station.pressurized_volume_m3` | 125 |
| `station.crew_capacity` | 4–8 |
| `station.ports` | 2 (docking) |
| `station.nasa_certified` | true |
| `station.launch_vehicle` | `falcon-heavy` |
| `station.consumable_crew_days` | 720 |

### Haven-2 full stack (`profiles/scenarios/haven2-growth-2028.yaml`)

| Milestone | Year | Modules | Crew vol (m³) | Station power (kW) | Cadence |
|-----------|------|---------|---------------|-------------------|---------|
| First module | 2028 | 1 | — | 9.8 | — |
| 2-module | +180d | 2 | — | 19.6 | ~6 mo |
| 3-module | +180d | 3 | — | 29 | |
| 4-module | 2030 | 4 | — | 39 | |
| Haven Core | 2030 | +core | 70 (core crew vol) | 7.3 (core only) | Starship-class event (public SpaceNews) |
| 9-module final | 2032 | 9 | 510 hab / 1160 press | 86 / 40 payload | target config |

Simulator treats each milestone as a **station state node**; `run` walks the timeline and evaluates queued `visits[]`.

---

## 4. Synthetic vehicle profiles (not proprietary)

These are **demo-only** YAML files labeled synthetic, shaped by public vehicle classes:

| Profile | Port type | Mass (kg) | CG offset (m) | Opening need (m) | Purpose |
|---------|-----------|-----------|---------------|------------------|---------|
| `crew-dragon-lda-gen1` | LDA gen-1 | 12000 | 0.4 axially | 2.0 pass-through | Crew swap on LDA |
| `crew-dragon-ida-heritage` | IDA | 12000 | 0.4 | 0.8 | Legacy port mismatch demo |
| `cargo-cbm-pallet` | CBM | 8000 | 0.6 | 1.6 | Opening / standard mismatch |
| `module-haven-2-expansion` | LDA androgynous | 29000 | 1.2 | 2.9 | Module-to-module dock |
| `heavy-visit-synthetic` | LDA gen-1 | 45000 | 0.8 | 2.5 | CG envelope exceedance demo |

Published bounds for doctor (synthetic until user guide parsed):

```yaml
# profiles/limits/idss-approach-bounds.yaml (SYNTHETIC — labeled in receipt)
approach:
  max_axial_rate_m_s: 0.05      # IDSS-class placeholder
  max_lateral_rate_m_s: 0.02
  max_roll_rate_deg_s: 0.3
capture:
  max_cg_offset_m: 0.5          # tunable; doctor flags exceedance
  max_vehicle_mass_kg: 40000    # order-of-magnitude for "large crewed vehicle" narrative
power_umbilical:
  required_connectors: [power, data, comms]
```

When the user guide is available, replace placeholders with cited tables in `assumptions[]` inside the receipt — never silently claim NASA exactitude.

---

## 5. Simulator pipeline (deterministic, no orbital mechanics)

```
plan(spec) → validated manifest + scenario hash
run(spec)  → timeline of visit events × station states
doctor()   → rule engine on single pairing OR full timeline
report()   → summary.json + report.md under out/receipts/<run-id>/
```

### `run` outputs per visit event

```json
{
  "visit_id": "fra-crew-2029-q2",
  "station_state": "haven2-3module",
  "port": "forward-lda",
  "vehicle": "crew-dragon-lda-gen1",
  "checks": {
    "interface_match": true,
    "opening_clearance": true,
    "approach_rates": true,
    "capture_envelope": true,
    "umbilical_checklist": true,
    "port_available": false
  },
  "verdict": "no-go",
  "blocking_reasons": ["port_double_booking"]
}
```

### Doctor rules (MVP — 20+ pytest targets)

| Rule ID | Trigger | Severity |
|---------|---------|----------|
| `LDA_GEN_MISMATCH` | `vehicle.lda_generation != port.lda_generation` | no-go |
| `PORT_STANDARD_MISMATCH` | vehicle port standard ∉ port.compatible_standards | no-go |
| `OPENING_UNDERSIZE` | `vehicle.min_opening_m > port.opening_diameter_m` | no-go |
| `CG_ENVELOPE_EXCEED` | `vehicle.cg_offset_m > limits.capture.max_cg_offset_m` | no-go |
| `MASS_CAP_EXCEED` | `vehicle.mass_kg > limits.capture.max_vehicle_mass_kg` | human-review |
| `APPROACH_RATE_EXCEED` | any approach rate > IDSS bounds | no-go |
| `SOFT_CAPTURE_INCOMPLETE` | checklist item false (retroreflector/latch/petal/actuator) | human-review |
| `HARD_CAPTURE_BOLT_MISMATCH` | bolt pattern incompatible | no-go |
| `UMBILICAL_MISSING` | required connector absent | human-review |
| `PORT_DOUBLE_BOOKING` | overlapping visits on same port | no-go |
| `MODULE_COUNT_UNDERFLOW` | station.modules < scenario requires | no-go |
| `TIMELINE_BEFORE_MODULE` | visit date before module online | no-go |
| `NASA_CERT_REQUIRED` | visit requires cert & station.nasa_certified false | human-review |
| `CONSUMABLE_CREW_DAYS` | visit duration > remaining crew-days | human-review |

---

## 6. Haven-scale worked example (demo script)

**File:** `examples/haven2-growth-2028.yaml`

```yaml
scenario: haven2-growth-2028
description: >
  Synthetic 2028–2032 growth with two international crew visits and one
  CBM-class cargo attempt. Demonstrates port booking + opening mismatch.

timeline:
  - date: 2028-06-01
    station_state: haven2-1module
  - date: 2029-01-15
    station_state: haven2-2module
  - date: 2029-06-01
    station_state: haven2-3module

visits:
  - id: uk-crew-2029-a
    date: 2029-06-10
    vehicle: crew-dragon-lda-gen1
    port: forward-lda
    duration_days: 14
  - id: fra-crew-2029-b
    date: 2029-06-12
    vehicle: crew-dragon-lda-gen1
    port: aft-lda
    duration_days: 14
  - id: cargo-cbm-2029
    date: 2029-06-15
    vehicle: cargo-cbm-pallet
    port: forward-lda
    duration_days: 7
```

**Expected doctor output:**
- `uk-crew-2029-a` + `cargo-cbm-2029` → `PORT_DOUBLE_BOOKING` on `forward-lda`
- `cargo-cbm-2029` → `OPENING_UNDERSIZE` if attempted on LDA (needs 1.6 m, has 2.9 m opening but **standard mismatch** on capture hardware → `PORT_STANDARD_MISMATCH`)

---

## 7. MVP package sketch

```
vast-docking-workbench/
  vast_dock/
    cli.py          # plan | run | doctor | report
    models.py       # Station, Vehicle, Visit, Port
    simulator.py    # timeline walk
    doctor.py       # rule engine
    receipt.py      # JSON + markdown emitter
  profiles/
    stations/
    vehicles/
    limits/
    scenarios/
  examples/
  tests/            # 20+ pytest on doctor rules
  pyproject.toml
```

**CLI:** `vast-dock` (package name `vast-docking-workbench`)  
**Site:** static demo consuming sample `summary.json` — `enaguthi.com/vast-docking-workbench/site/`

---

## 8. Outreach angle (post-MVP)

> Built an open Station Docking Compatibility Workbench (plan/run/doctor/report) using your published LDA interface dimensions and Haven/Haven-2 specs — receipts flag generation mismatch, CG envelope, and berthing timeline conflicts before integration review. Demo: https://enaguthi.com/vast-docking-workbench/site/

---

## 9. Open questions before coding

1. **Parse user guide PDF** when downloaded — extract numeric tables into `profiles/limits/lda-gen-1.yaml` with page citations.
2. **Haven-1 port standard** — website shows fit-check on passive docking hardware; confirm IDA vs LDA in receipt assumptions until clarified publicly.
3. **Haven Core 7 m cross** — SpaceNews architecture detail; optional v0.2 scenario node (not MVP).
