"""Batch entrypoint for Cloudera Jobs: python -m banksynth.cli --output portfolio.zip."""
import argparse
import json
from pathlib import Path
from banksynth.engine import Config
from banksynth.catalog import DEFAULT_FIELDS
from banksynth.field_engine import generate_selected
from dataclasses import replace
from banksynth.quality import evaluate
from banksynth.export import bundle


def main():
    parser = argparse.ArgumentParser(description="Generate a synthetic banking portfolio")
    parser.add_argument("--config", type=Path, help="JSON configuration exported by the UI")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = Config(**json.loads(args.config.read_text())) if args.config else Config()
    if cfg.selected_fields is None:
        cfg = replace(cfg, selected_fields=DEFAULT_FIELDS)
    tables, checks = generate_selected(cfg, cfg.selected_fields)
    if not all(c["passed"] for c in checks):
        raise RuntimeError("Validation failed; export blocked")
    payload = bundle(tables, cfg, checks)
    with args.output.open("xb") as handle:
        handle.write(payload)
    print(f"Exported {sum(map(len, tables.values())):,} records to {args.output}")

if __name__ == "__main__":
    main()
