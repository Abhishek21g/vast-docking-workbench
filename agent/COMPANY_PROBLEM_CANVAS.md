# Vast Space — Problem Canvas

**Product (Track B):** Station Docking Compatibility Workbench  
**PR (Track A):** None — no public engineering GitHub (LDA interface user guide is website-only)  
**Workspace:** `~/Documents/vast-space` · `~/vast`  
**Gold references:** tinker-workbench · sia-eval-harness  
**Outreach:** info@vastspace.com

---

## 1. What is the company solving? (one sentence)

Vast is building **America's next commercial space-station platform** — Haven-1 first (2027), then modular Haven-2 as the ISS successor (2028–2032) — while open-sourcing the **Large Docking Adapter (LDA)** so the entire LEO ecosystem (crew vehicles, cargo, international modules) can attach to Vast and to each other at scale.

---

## 2. Who is the customer / user?

| User | What they do | What growth depends on |
|------|--------------|------------------------|
| **Vast exec / BD** | Win NASA CLD Phase 2 (~mid-2026), sign France/UK/Czech/ESA partners, sell station capacity | Prove Haven-2 can absorb ISS-scale traffic without docking/integration surprises |
| **Vast mission ops / integration** | Plan Haven-1 crew visits, Haven-2 module launches every ~180 days, port scheduling | Every berthing is a go/no-go on timeline, CG envelope, power/data umbilical |
| **LDA adopters** (vehicle OEMs, station competitors, agencies) | Download interface user guide, purchase or self-build LDA hardware | Self-certify against published geometry without proprietary Haven CAD |
| **NASA / international anchor customers** | Evaluate CLD proposals, certify for NASA astronauts | Docking cadence, EVA, multi-port ops, microgravity lab continuity post-ISS |

**Primary product user for the demo:** a Vast BD or mission-integration lead (or a partner vehicle PM) who needs a **receipt-grade answer** to "can this vehicle dock this module on this date?" before committing schedule or capital.

---

## 3. What pain do they publicly describe? (quote + source)

> "Future space stations will use larger modules, have greater overall mass, and dock with a new generation of bigger crewed vehicles. **New docking standards and universal hardware are required** for the future generation of space vehicles and habitats."

> "By open-sourcing the interface, Vast is intending to **encourage industry-wide collaboration and accelerate the development of interoperable space systems**."

— [Vast Unveils a Large Docking Adapter Standard](https://www.vastspace.com/updates/vast-unveils-a-large-docking-adapter-standard) (April 15, 2026)

> "Supports **2 to 20+ modules** … **Compatible with IDSS approach rates and loads** … **Large crewed vehicle-to-station docking** capability."

— [Large Docking Adapter](https://www.vastspace.com/large-docking-adapter)

> "Starting in 2028, Haven Modules will launch **approximately every six months**, with a final station configuration slated for 2032."

— [Haven-2](https://www.vastspace.com/haven-2)

> "We operate under the assumption that we are **all-in on winning CLD**."

— Max Haot, SpaceNews interview on Haven-2 ([SpaceNews, Oct 2024](https://spacenews.com/vast-releases-design-of-haven-2-commercial-space-station/))

> "The freedom that comes on a commercial platform … includes missions that are **making goods to sell back on Earth**, and **ownership of the intellectual property** created aboard the habitat."

— CEO Max Haot, press coverage cited on [vastspace.com](https://www.vastspace.com/)

**Synthesis (executive lens):** Vast's growth is not "launch one station." It is **(a)** win CLD, **(b)** fill modular capacity with gov + commercial customers, **(c)** make LDA the **default attach point** for the post-ISS fleet. Publicly they name interoperability and scale; privately every failed compatibility review slows partner signings and module-integration cadence.

---

## 4. What gap exists today?

| What they ship | What's missing |
|----------------|----------------|
| LDA interface **user guide** (download, May 2026) | No public **compatibility simulator** — partners must infer pass/fail from PDF geometry + email Vast |
| Haven-1 / Haven-2 **published specs** (mass, ports, volume, timeline) | No **receipt trail** for "vehicle X + module Y + port Z → dock-go / human-review / no-go" |
| Haven Demo **flight heritage** (2025 success) | No tool tying **modular growth timeline** (9-module Haven-2) to **concurrent partner visit** constraints |
| International MoUs (France, UK, Czech/ESA) | No shared **pre-flight checklist** artifact agencies can run before mission commitment |
| IDSS heritage claim on LDA | No automated check that a vehicle's **approach rates, CG envelope, capture loads** stay inside published bounds |

**The big gap (why this helps them grow):** Vast is trying to become the **USB-C of orbital docking** — but standards only win when adoption friction is near zero. Today a partner's integration engineer reads the user guide and hopes. A workbench that outputs **JSON receipts** turns LDA from "interesting press release" into **infrastructure developers can CI against**, which accelerates the network effect Vast needs to beat Axiom, Starlab, and Orbital Reef for mindshare and port count.

---

## 5. Product thesis (one sentence)

**We built the Station Docking Compatibility Workbench so that Vast and LDA adopters can pre-certify vehicle–module–port pairings and modular station growth timelines without waiting on bespoke integration reviews or proprietary Haven CAD.**

### Bigger framing (executive demo narrative)

Think of it as a **"LEO attach-point growth model"** in CLI form:

- **Plan** — declare a *growth scenario*: which Haven modules exist, which ports are LDA/IDA/CBM-class, which partner vehicles arrive when (crew Dragon-class, cargo, future heavy vehicles).
- **Run** — deterministic compatibility sim: interface match, capture envelope, consumable/crew-day budget after dock, power umbilical checklist.
- **Doctor** — flags blockers to **network growth**: LDA generation mismatch, CG exceedance, port double-booking during 180-day module cadence, pressurized opening too small for declared cargo, IDSS approach-rate violation.
- **Report** — receipt JSON: `dock-go` | `human-review` | `no-go` + assumption log (every number labeled synthetic/public-source).

**"Impossible but useful" demo hook:** simulate **full Haven-2 9-module assembly (2028–2032)** with France/UK/Czech visit manifests and show which quarters are **structurally dockable but operationally no-go** because both Haven-2 ports are booked — the kind of scheduling collision that kills partner confidence but never appears in a static brochure.

This is NOT claiming Vast partnership. It uses **only** published LDA geometry, Haven/Haven-2 specs, and synthetic vehicle YAML profiles.

---

## 6. Why this is NOT the PR

- **PR fixes:** Nothing — no public upstream repo. (Revisit only if Vast publishes LDA CAD/reference implementations to GitHub.)
- **Product solves:** **Ecosystem adoption + mission-integration risk** for a station company whose moat is **interfaces and modular growth**, not a single launch.

If LDA were on GitHub, a PR might fix a dimension typo in the guide. The product answers: **"Given these public constraints, does this docking campaign close?"** — a BD/ops question, not a doc patch.

---

## 7. Mock demo (60-second run for a hiring manager)

```bash
pip install -e .
vast-dock plan examples/haven2-growth-2028.yaml
vast-dock run  examples/haven2-growth-2028.yaml --seed 42
vast-dock doctor examples/haven2-growth-2028.yaml --vehicle crew-dragon-lda-gen1 --port forward-lda
vast-dock report --json out/receipts/latest/summary.json
```

**Worked scenario:** Haven-1 scale vehicle attempts LDA gen-1 dock to forward port while a **CBM-class cargo pallet** is queued same week → doctor flags **pressurized opening mismatch** + **berthing timeline conflict** → report `no-go` with cited public LDA opening (2.90 m) vs CBM heritage (1.6 m).

**Target URL:** `enaguthi.com/vast-docking-workbench/site/`

---

## Appendix A — Public facts → why the product maps to growth

| Public milestone | Growth stake | Workbench angle |
|------------------|--------------|-----------------|
| Haven Demo success (Nov 2025) | Only commercial station co. to fly own spacecraft | Proves sim params can anchor on real Vast heritage |
| Haven-1 NET 2027, 1 port, 14.6 t | First revenue / crew visits | Single-port scheduling doctor |
| LDA standard + user guide (Apr/May 2026) | Standard-setter play | Interface-match rules from published geometry |
| Haven-2 CLD bid, 2 ports, 9 modules by 2032 | Company-defining contract | Multi-module growth + port double-booking doctor |
| France 2-mission, UK MoU, Czech/ESA ISS path | International pipeline | Vehicle profile library (synthetic) |
| "Purchase adapter OR manufacture your own" | Hardware + IP licensing | Receipt shows *interface* pass independent of vendor |

---

## Appendix B — LDA public claims → simulator parameters

See `agent/TARGET_BRIEF_VAST.md` for full param table, doctor rules, and YAML schema sketch.

**Sources (public only):**
- https://www.vastspace.com/
- https://www.vastspace.com/large-docking-adapter
- https://www.vastspace.com/updates/vast-unveils-a-large-docking-adapter-standard
- https://www.vastspace.com/haven-2
- https://spacenews.com/vast-releases-design-of-haven-2-commercial-space-station/

**Do NOT use:** proprietary Haven CAD, unreleased user-guide sections, or vast-data (storage company).
