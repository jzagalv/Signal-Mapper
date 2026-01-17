from __future__ import annotations

import json

from domain.models import Project, Bay, Device, Signal, SignalEnd, CanvasLayout, SignalTemplate
from domain.services.interlock_service import normalize_interlocks, serialize_interlocks


def load_project(path: str) -> Project:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    project = Project(schema_version=meta.get("schema_version", "1.0.0"), name=meta.get("name", "Proyecto"))

    for b in data.get("project", {}).get("bays", []):
        project.bays[b["bay_id"]] = Bay(bay_id=b["bay_id"], name=b.get("name", b["bay_id"]))

    for t in data.get("project", {}).get("templates", []):
        project.templates.append(
            SignalTemplate(
                code=t["code"],
                label=t.get("label", t["code"]),
                nature=t.get("nature", "DIGITAL"),
                category=t.get("category", "General"),
                description=t.get("description", ""),
            )
        )

    signals_by_id = {}
    for s in data.get("project", {}).get("signals", []):
        signals_by_id[s["signal_id"]] = Signal(
            signal_id=s["signal_id"],
            name=s.get("name", s["signal_id"]),
            nature=s.get("nature", "DIGITAL"),
            description=s.get("description", ""),
        )

    for d in data.get("project", {}).get("devices", []):
        dev = Device(
            device_id=d["device_id"],
            bay_id=d["bay_id"],
            name=d.get("name", d["device_id"]),
            dev_type=d.get("type", "IED"),
        )

        for e in d.get("inputs", []):
            dev.inputs.append(
                SignalEnd(
                    signal_id=e["signal_id"],
                    direction="IN",
                    text=e.get("text", ""),
                    status=e.get("status", "CONFIRMED"),
                    test_block=False,  # no aplica en IN
                    interlocks=normalize_interlocks(e.get("interlocks")),
                )
            )

        for e in d.get("outputs", []):
            dev.outputs.append(
                SignalEnd(
                    signal_id=e["signal_id"],
                    direction="OUT",
                    text=e.get("text", ""),
                    status=e.get("status", "CONFIRMED"),
                    test_block=bool(e.get("test_block", False)),
                    interlocks=None,  # no aplica en OUT
                )
            )

        if dev.bay_id not in project.bays:
            project.bays[dev.bay_id] = Bay(bay_id=dev.bay_id, name=dev.bay_id)
        project.bays[dev.bay_id].devices[dev.device_id] = dev

    # asigna señales usadas a cada bahía
    for bay in project.bays.values():
        used = set()
        for dev in bay.devices.values():
            for e in dev.inputs + dev.outputs:
                used.add(e.signal_id)
        for sid in used:
            if sid in signals_by_id:
                bay.signals[sid] = signals_by_id[sid]

    for c in data.get("project", {}).get("canvases", []):
        project.canvases[c["bay_id"]] = CanvasLayout(
            bay_id=c["bay_id"],
            zoom=c.get("zoom", 1.0),
            pan_x=c.get("pan", {}).get("x", 0.0),
            pan_y=c.get("pan", {}).get("y", 0.0),
            device_positions=c.get("device_positions", {}),
        )

    return project


def save_project(project: Project, path: str) -> None:
    out = {
        "meta": {"schema_version": project.schema_version, "name": project.name},
        "project": {"bays": [], "signals": [], "devices": [], "canvases": [], "templates": []},
    }

    for bay in project.bays.values():
        out["project"]["bays"].append({"bay_id": bay.bay_id, "name": bay.name})

    for t in project.templates:
        out["project"]["templates"].append(
            {
                "code": t.code,
                "label": t.label,
                "nature": t.nature,
                "category": t.category,
                "description": t.description,
            }
        )

    seen = set()
    for bay in project.bays.values():
        for sig in bay.signals.values():
            if sig.signal_id in seen:
                continue
            seen.add(sig.signal_id)
            out["project"]["signals"].append(
                {
                    "signal_id": sig.signal_id,
                    "name": sig.name,
                    "nature": sig.nature,
                    "description": sig.description,
                }
            )

    for bay in project.bays.values():
        for dev in bay.devices.values():
            out["project"]["devices"].append(
                {
                    "device_id": dev.device_id,
                    "bay_id": dev.bay_id,
                    "name": dev.name,
                    "type": dev.dev_type,
                    "inputs": [
                        {
                            "signal_id": e.signal_id,
                            "text": e.text,
                            "status": e.status,
                            "test_block": False,
                            "interlocks": serialize_interlocks(getattr(e, "interlocks", None)),
                        }
                        for e in dev.inputs
                    ],
                    "outputs": [
                        {
                            "signal_id": e.signal_id,
                            "text": e.text,
                            "status": e.status,
                            "test_block": bool(getattr(e, "test_block", False)),
                            "interlocks": [],
                        }
                        for e in dev.outputs
                    ],
                }
            )

    for bay_id, layout in project.canvases.items():
        out["project"]["canvases"].append(
            {
                "bay_id": bay_id,
                "zoom": layout.zoom,
                "pan": {"x": layout.pan_x, "y": layout.pan_y},
                "device_positions": layout.device_positions,
            }
        )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
