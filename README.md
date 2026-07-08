# Vast Space — Station Docking Compatibility Workbench

Open CLI for **plan → run → doctor → report** docking compatibility checks using **published** [Vast Large Docking Adapter](https://www.vastspace.com/large-docking-adapter) geometry and Haven/Haven-2 specs.

> **Not affiliated with Vast Space.** Synthetic vehicle profiles; no proprietary Haven CAD.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

vast-dock plan examples/haven2-growth-2028.yaml
vast-dock run  examples/haven2-growth-2028.yaml --seed 42
vast-dock doctor examples/haven2-growth-2028.yaml
vast-dock report --json out/receipts/latest/summary.json

pytest -q
```

## Commands

| Command | Purpose |
|---------|---------|
| `plan` | Validate scenario YAML, emit manifest + hash |
| `run` | Walk growth timeline, evaluate visits, write receipt JSON |
| `doctor` | Full scenario doctor or single `--vehicle` / `--port` pairing |
| `report` | Render markdown (or pass through `--json`) from summary |

Receipts land in `out/receipts/<run-id>/summary.json` with a `latest/` symlink copy.

## Demo scenario

`examples/haven2-growth-2028.yaml` models Haven-2 growth with UK/French crew visits plus a CBM-class cargo attempt. Expected doctor flags:

- `PORT_DOUBLE_BOOKING` — overlapping `forward-lda` visits
- `PORT_STANDARD_MISMATCH` — CBM pallet on LDA port

## Public sources

- https://www.vastspace.com/large-docking-adapter
- https://www.vastspace.com/updates/vast-unveils-a-large-docking-adapter-standard
- https://www.vastspace.com/haven-2

## Site

Interactive demo: https://enaguthi.com/vast-docking-workbench/site/

## License

MIT
