import hashlib
import io
import json
import zipfile
import sys
from importlib.metadata import version
from dataclasses import asdict
from banksynth import __version__
from banksynth.catalog import BY_ID, PRIMARY_KEYS


def bundle(tables, config, checks, mode="Simulator", comparison=None):
    output = io.BytesIO()
    actual = [f"{table}.{col}" for table, frame in tables.items() for col in frame]
    selected = list(config.selected_fields) if config.selected_fields is not None else actual
    relationships = []
    for fid in actual:
        field = BY_ID.get(fid)
        if field and field.rule.startswith("fk:"):
            parent = field.rule[3:]
            if parent in tables:
                relationships.append(f"{fid} -> {parent}.{PRIMARY_KEYS[parent]}")
    manifest = {"generator_version": __version__, "catalog_version": "2.0-500",
        "runtime": {"python": sys.version.split()[0], "numpy": version("numpy"), "pandas": version("pandas"), "sdv": version("sdv") if mode != "Simulator" else None},
        "config": asdict(config), "engine": mode, "selected_fields": selected,
        "supporting_keys": [fid for fid in actual if fid not in selected],
        "privacy": "No real data used" if mode == "Simulator" else "SDV reference-trained; not differentially private; disclosure review required",
        "limitations": "Curated illustrative field rules, not an industry ranking or calibration to real bank behavior. Non-ledger domains are test snapshots, not a complete banking accounting model. SDV learns only customer age, income and credit score.",
        "tables": {}, "checks": checks, "reference_comparison": comparison, "relationships": relationships}
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, frame in tables.items():
            content = frame.to_csv(index=False).encode("utf-8")
            archive.writestr(f"{name}.csv", content)
            manifest["tables"][name] = {"rows": len(frame), "sha256": hashlib.sha256(content).hexdigest(), "columns": {k: str(v) for k, v in frame.dtypes.items()}}
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        definitions = [{"field_id": fid, "type": BY_ID[fid].dtype, "description": BY_ID[fid].description, "source": "selected" if fid in selected else "supporting key"} for fid in actual if fid in BY_ID]
        archive.writestr("field_definitions.json", json.dumps(definitions, indent=2))
        archive.writestr("README.txt", "SYNTHETIC TEST DATA\nOnly selected fields and supporting join keys are exported. See manifest.json and field_definitions.json for schema, assumptions, validation and hashes.\nAll identities and credential-like fields are test-only. Non-ledger domains are illustrative snapshots.\n")
    return output.getvalue()
