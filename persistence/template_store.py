from __future__ import annotations

import json
import os
from dataclasses import asdict

from domain.models import SignalTemplate

FILENAME = "template_library.json"


def _path(app_dir: str) -> str:
    return os.path.join(app_dir, FILENAME)


def _default_templates() -> list[SignalTemplate]:
    return [
        SignalTemplate(code="ALM_DC_LOW", label="Alarma DC bajo", category="Alarmas", nature="DIGITAL", description=""),
        SignalTemplate(code="CLOSE_52", label="Mando Cierre", category="Mandos", nature="DIGITAL", description=""),
        SignalTemplate(code="OPEN_52", label="Mando Apertura", category="Mandos", nature="DIGITAL", description=""),
        SignalTemplate(code="VOLT_BUS_AI", label="Tensión barra", category="Mediciones", nature="ANALOG", description=""),
        SignalTemplate(code="50BF_START", label="Arranque 50BF", category="Protecciones", nature="DIGITAL", description=""),
        SignalTemplate(code="TRIP_52", label="Trip 52", category="Protecciones", nature="DIGITAL", description=""),
        SignalTemplate(code="RETRIP_52", label="Retrip", category="Protecciones", nature="DIGITAL", description=""),
    ]


def load_global_templates(app_dir: str) -> list[SignalTemplate]:
    path = _path(app_dir)
    if not os.path.exists(path):
        templates = _default_templates()
        save_global_templates(app_dir, templates)
        return templates

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("templates", data if isinstance(data, list) else [])
        templates = []
        for t in items:
            # compatibilidad: si venía 'name' lo tomamos como label
            if "label" not in t and "name" in t:
                t = dict(t)
                t["label"] = t["name"]
            templates.append(SignalTemplate(
                code=t["code"],
                label=t.get("label", t["code"]),
                nature=t.get("nature", "DIGITAL"),
                category=t.get("category", "General"),
                description=t.get("description", ""),
            ))
        if not templates:
            templates = _default_templates()
            save_global_templates(app_dir, templates)
        return templates
    except Exception:
        templates = _default_templates()
        save_global_templates(app_dir, templates)
        return templates


def save_global_templates(app_dir: str, templates: list[SignalTemplate]) -> None:
    path = _path(app_dir)
    payload = {"templates": [asdict(t) for t in templates]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
