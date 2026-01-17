from __future__ import annotations
from copy import deepcopy
import re
from domain.models import Bay, Device, Signal, SignalEnd, CanvasLayout

def _unique_bay_id(project, base: str) -> str:
    if base not in project.bays:
        return base
    i = 2
    while True:
        cand = f"{base}-{i}"
        if cand not in project.bays:
            return cand
        i += 1

def _unique_device_id(bay: Bay, base: str) -> str:
    if base not in bay.devices:
        return base
    i = 2
    while True:
        cand = f"{base}-{i}"
        if cand not in bay.devices:
            return cand
        i += 1

def generate_unique_signal_id(project, bay_id: str) -> str:
    existing=set()
    for b in project.bays.values():
        existing.update(b.signals.keys())
    i = 1
    while True:
        cand = f"{bay_id}-SIG-{i:03d}"
        if cand not in existing:
            return cand
        i += 1

def _replace_token(text: str, src_token: str, dst_token: str) -> str:
    if not text or not src_token or not dst_token:
        return text
    # replace case-insensitive, preserving dst token exactly as typed
    return re.sub(re.escape(src_token), dst_token, text, flags=re.IGNORECASE)

def replicate_bay(
    project,
    src_bay_id: str,
    new_bay_id: str,
    new_bay_name: str,
    *,
    copy_signals: bool=True,
    dx: float=80.0,
    dy: float=60.0,
    src_token: str="",
    dst_token: str="",
    apply_to_external: bool=True,
):
    src = project.bays[src_bay_id]
    new_bay_id = _unique_bay_id(project, new_bay_id)
    dst = Bay(bay_id=new_bay_id, name=new_bay_name)
    project.bays[new_bay_id] = dst

    # layout
    src_layout = project.canvases.get(src_bay_id)
    if src_layout:
        dst_layout = CanvasLayout(
            bay_id=new_bay_id, zoom=src_layout.zoom, pan_x=src_layout.pan_x, pan_y=src_layout.pan_y, device_positions={}
        )
        project.canvases[new_bay_id] = dst_layout
    else:
        project.canvases[new_bay_id] = CanvasLayout(bay_id=new_bay_id)

    # device mapping
    id_map = {}
    name_map = {}

    for dev in src.devices.values():
        base_id = dev.device_id.replace(src_bay_id, new_bay_id)
        base_id = _replace_token(base_id, src_token, dst_token)
        new_id = _unique_device_id(dst, base_id)

        new_name = dev.name
        # Prefer token replacement (e.g., 52H1 -> 52H2, PS1-H1 -> PS1-H2)
        new_name = _replace_token(new_name, src_token, dst_token)
        if new_name == dev.name:
            # fallback: append new bay name
            new_name = f"{dev.name}-{new_bay_name}"

        dst_dev = Device(device_id=new_id, bay_id=new_bay_id, name=new_name, dev_type=dev.dev_type)
        dst.devices[new_id] = dst_dev

        id_map[dev.device_id] = new_id
        name_map[dev.name] = new_name

        if src_layout and dev.device_id in src_layout.device_positions:
            p = src_layout.device_positions[dev.device_id]
            project.canvases[new_bay_id].device_positions[new_id] = {"x": float(p.get("x", 200.0)+dx), "y": float(p.get("y", 200.0)+dy)}
        else:
            project.canvases[new_bay_id].device_positions[new_id] = {"x": 240.0, "y": 220.0}

    if not copy_signals:
        return new_bay_id

    def rewrite_endpoint(text: str) -> tuple[str, str|None]:
        """Reescribe el texto del chip para la bahía replicada.

        Regla de ingeniería:
        - Enlaces internos (a equipos que existen en la bahía) se mantienen CONFIRMED y se ajustan al nuevo nombre.
        - Enlaces externos se marcan PENDING.
        """
        # 1) apply token replacement to whole text (left + right)
        t = _replace_token(text, src_token, dst_token) if (src_token and dst_token) else text

        if " hacia " in t:
            left, right = t.split(" hacia ", 1)
            right_clean = right.replace("(pendiente)", "").strip()

            # Internal: if the RHS is an old device name, map to the new name.
            if right_clean in name_map:
                return f"{left.strip()} hacia {name_map[right_clean]}", None
            # Or already matches a new name
            if right_clean in name_map.values():
                return f"{left.strip()} hacia {right_clean}", None

            # External
            if apply_to_external:
                return f"{left.strip()} hacia {right_clean} (pendiente)", "PENDING"
            return f"{left.strip()} hacia EXTERNO (pendiente)", "PENDING"

        if " desde " in t:
            left, right = t.split(" desde ", 1)
            right_clean = right.replace("(pendiente)", "").strip()

            if right_clean in name_map:
                return f"{left.strip()} desde {name_map[right_clean]}", None
            if right_clean in name_map.values():
                return f"{left.strip()} desde {right_clean}", None

            if apply_to_external:
                return f"{left.strip()} desde {right_clean} (pendiente)", "PENDING"
            return f"{left.strip()} desde EXTERNO (pendiente)", "PENDING"

        return t, None

    # --- Sub-equivalence (SignalID lógico) ---
    # Cada SignalID de la bahía fuente se mapea a UN SOLO SignalID nuevo en la bahía destino,
    # y todos sus extremos (IN/OUT) apuntan al mismo ID.

    signal_id_map: dict[str, str] = {}

    def _map_signal_id(old_signal_id: str, sample_text: str) -> str:
        if old_signal_id in signal_id_map:
            return signal_id_map[old_signal_id]

        sid = generate_unique_signal_id(project, new_bay_id)
        signal_id_map[old_signal_id] = sid

        old_sig = src.signals.get(old_signal_id)
        sig_name = old_sig.name if old_sig else _infer_name_from_text(sample_text)
        sig_nature = old_sig.nature if old_sig else "DIGITAL"
        sig_name = _replace_token(sig_name, src_token, dst_token)

        dst.signals[sid] = Signal(signal_id=sid, name=sig_name, nature=sig_nature)
        return sid

    # Clone endpoints while preserving logical equivalence.
    for old_dev in src.devices.values():
        new_dev = dst.devices[id_map[old_dev.device_id]]

        for e in old_dev.inputs:
            sid = _map_signal_id(e.signal_id, e.text)
            new_text, force = rewrite_endpoint(e.text)
            new_dev.inputs.append(
                SignalEnd(
                    signal_id=sid,
                    direction="IN",
                    text=new_text,
                    status=force or e.status,
                    test_block=bool(getattr(e, "test_block", False)),
                    interlocks=deepcopy(getattr(e, "interlocks", None)),
                )
            )

        for e in old_dev.outputs:
            sid = _map_signal_id(e.signal_id, e.text)
            new_text, force = rewrite_endpoint(e.text)
            new_dev.outputs.append(
                SignalEnd(
                    signal_id=sid,
                    direction="OUT",
                    text=new_text,
                    status=force or e.status,
                    test_block=bool(getattr(e, "test_block", False)),
                    interlocks=deepcopy(getattr(e, "interlocks", None)),
                )
            )

    return new_bay_id

def _infer_name_from_text(text: str) -> str:
    if " hacia " in text:
        return text.split(" hacia ", 1)[0].strip()
    if " desde " in text:
        return text.split(" desde ", 1)[0].strip()
    return text.strip() or "SIN_NOMBRE"
