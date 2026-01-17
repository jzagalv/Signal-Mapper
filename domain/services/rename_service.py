from __future__ import annotations

from typing import Optional


def _replace_after_keyword(text: str, keyword: str, old: str, new: str) -> str:
    """Reemplaza el nombre del equipo en patrones '... <keyword> <device_name>[ ...]'.

    Preserva sufijos como '(pendiente)' u otros detalles.
    """
    if not text or keyword not in text:
        return text
    left, suffix = text.split(keyword, 1)
    suffix = suffix.lstrip()
    if not suffix:
        return text

    # Si el sufijo empieza con el nombre antiguo, lo reemplazamos y preservamos resto.
    if suffix.startswith(old):
        rest = suffix[len(old):]
        return f"{left}{keyword} {new}{rest}"
    return text


def rename_device_in_project(project, *, bay_id: str, device_id: str, new_name: str) -> None:
    """Renombra un equipo y actualiza referencias visibles ('desde/hacia <equipo>').

    NOTA: IDs NO cambian. Sólo se actualiza Device.name y textos de SignalEnd.
    """
    bay = project.bays.get(bay_id)
    if not bay or device_id not in bay.devices:
        raise ValueError("No se encontró el equipo para renombrar.")

    dev = bay.devices[device_id]
    old_name = dev.name
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("Nombre de equipo vacío.")

    if new_name == old_name:
        return

    # 1) renombra el equipo
    dev.name = new_name

    # 2) actualiza referencias en TODO el proyecto (otros equipos pueden referenciar por nombre)
    for b in project.bays.values():
        for d in b.devices.values():
            for e in d.outputs:
                e.text = _replace_after_keyword(e.text, " hacia ", old_name, new_name)
            for e in d.inputs:
                e.text = _replace_after_keyword(e.text, " desde ", old_name, new_name)


def rename_bay(project, *, bay_id: str, new_name: str) -> None:
    bay = project.bays.get(bay_id)
    if not bay:
        raise ValueError("No se encontró la bahía.")
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("Nombre de bahía vacío.")
    bay.name = new_name
