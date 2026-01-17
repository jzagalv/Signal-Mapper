from __future__ import annotations

from typing import Any, List, Optional

from domain.models import InterlockItem, InterlockSpec


def normalize_interlocks(raw: Any) -> Optional[InterlockSpec]:
    """Normaliza enclavamientos desde JSON/legacy.

    Acepta:
    - None
    - list[str] (legacy)
    - dict con {mode, items}

    Retorna InterlockSpec o None.
    """
    if raw is None:
        return None

    # legacy: list[str]
    if isinstance(raw, list):
        items: List[InterlockItem] = []
        for it in raw:
            if isinstance(it, str) and it.strip():
                items.append(InterlockItem(relay_tag=it.strip(), category="Bloqueos"))
        return InterlockSpec(mode="AND", items=items) if items else None

    if isinstance(raw, dict):
        mode = raw.get("mode", "AND")
        raw_items = raw.get("items", [])
        items: List[InterlockItem] = []
        if isinstance(raw_items, list):
            for it in raw_items:
                if isinstance(it, dict):
                    relay_tag = str(it.get("relay_tag", "")).strip()
                    if not relay_tag:
                        # lo validamos aguas abajo; aquí simplemente lo omitimos
                        continue
                    items.append(
                        InterlockItem(
                            relay_tag=relay_tag,
                            category=str(it.get("category", "Bloqueos")),
                            source_device_id=it.get("source_device_id"),
                            source_signal_id=it.get("source_signal_id"),
                        )
                    )
                elif isinstance(it, str) and it.strip():
                    items.append(InterlockItem(relay_tag=it.strip(), category="Bloqueos"))

        return InterlockSpec(mode=mode if mode in ("AND", "OR") else "AND", items=items) if items else None

    # tipo inesperado
    return None


def interlock_tags(spec: Optional[InterlockSpec]) -> List[str]:
    if not spec or not spec.items:
        return []
    return [i.relay_tag for i in spec.items if (i.relay_tag or "").strip()]


def serialize_interlocks(spec: Optional[InterlockSpec]) -> Any:
    if not spec or not spec.items:
        return []
    return {
        "mode": spec.mode,
        "items": [
            {
                "relay_tag": i.relay_tag,
                "category": i.category,
                "source_device_id": i.source_device_id,
                "source_signal_id": i.source_signal_id,
            }
            for i in spec.items
        ],
    }


def validate_interlocks(spec: Optional[InterlockSpec]) -> None:
    """Valida reglas de dominio. Lanza ValueError si inválido."""
    if spec is None:
        return
    for idx, it in enumerate(spec.items):
        if not (it.relay_tag or "").strip():
            raise ValueError(f"Enclavamiento inválido en posición {idx+1}: falta relay_tag (ej: 86T2).")
