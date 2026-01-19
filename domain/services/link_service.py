from __future__ import annotations
from domain.models import SignalEnd

def remove_link(bay, signal_id: str) -> None:
    for dev in bay.devices.values():
        dev.inputs[:] = [e for e in dev.inputs if e.signal_id != signal_id]
        dev.outputs[:] = [e for e in dev.outputs if e.signal_id != signal_id]
    if signal_id in bay.signals:
        del bay.signals[signal_id]

def recognize_pending_link(bay, origin_device_id: str, signal_id: str, dest_device_id: str) -> None:
    origin = bay.devices[origin_device_id]
    dest = bay.devices[dest_device_id]
    sig = bay.signals.get(signal_id)
    sig_name = sig.name if sig else signal_id

    for e in origin.outputs:
        if e.signal_id == signal_id:
            left = sig_name
            if " hacia " in e.text:
                left, _ = e.text.split(" hacia ", 1)
                left = left.strip()
            e.text = f"{left} hacia {dest.name}"
            e.status = "CONFIRMED"

    for e in dest.inputs:
        if e.signal_id == signal_id:
            return

    dest.inputs.append(SignalEnd(
        signal_id=signal_id,
        direction="IN",
        text=f"{sig_name} desde {origin.name}",
        status="CONFIRMED"
    ))

def rename_signal_texts(bay, signal_id: str, new_name: str) -> None:
    if signal_id in bay.signals:
        bay.signals[signal_id].name = new_name

    for dev in bay.devices.values():
        for e in dev.outputs:
            if e.signal_id != signal_id:
                continue
            if " hacia " in e.text:
                _, suffix = e.text.split(" hacia ", 1)
                e.text = f"{new_name} hacia {suffix.strip()}"
            else:
                e.text = new_name

        for e in dev.inputs:
            if e.signal_id != signal_id:
                continue
            if " desde " in e.text:
                _, suffix = e.text.split(" desde ", 1)
                e.text = f"{new_name} desde {suffix.strip()}"
            else:
                e.text = new_name


def find_signal_destination_device_id(bay, signal_id: str) -> str | None:
    for dev in bay.devices.values():
        for e in dev.inputs:
            if e.signal_id == signal_id:
                return dev.device_id
    return None


def _infer_origin_name(bay, signal_id: str, origin_device_id: str | None) -> str | None:
    if origin_device_id and origin_device_id in bay.devices:
        return bay.devices[origin_device_id].name
    for dev in bay.devices.values():
        for e in dev.outputs:
            if e.signal_id == signal_id:
                return dev.name
    for dev in bay.devices.values():
        for e in dev.inputs:
            if e.signal_id == signal_id and " desde " in e.text:
                _, suffix = e.text.split(" desde ", 1)
                name = suffix.replace("(pendiente)", "").strip()
                if name:
                    return name
    return None


def update_signal_destination(
    bay,
    signal_id: str,
    dest_device_id: str | None,
    *,
    origin_device_id: str | None = None,
) -> None:
    sig = bay.signals.get(signal_id)
    sig_name = sig.name if sig else signal_id
    origin_name = _infer_origin_name(bay, signal_id, origin_device_id)

    if dest_device_id is None:
        dest_name = "EXTERNO"
    else:
        dest = bay.devices.get(dest_device_id)
        if not dest:
            return
        dest_name = dest.name

    # Update outputs (optionally only from one origin device).
    for dev in bay.devices.values():
        if origin_device_id and dev.device_id != origin_device_id:
            continue
        for e in dev.outputs:
            if e.signal_id != signal_id:
                continue
            if dest_device_id is None:
                e.status = "PENDING"
                e.text = f"{sig_name} hacia {dest_name} (pendiente)"
            else:
                e.status = "CONFIRMED"
                e.text = f"{sig_name} hacia {dest_name}"

    # Update inputs (single destination per bay).
    for dev in bay.devices.values():
        if dest_device_id is None or dev.device_id != dest_device_id:
            dev.inputs[:] = [e for e in dev.inputs if e.signal_id != signal_id]
            continue

        end = next((e for e in dev.inputs if e.signal_id == signal_id), None)
        text = f"{sig_name} desde {origin_name}" if origin_name else sig_name
        if end:
            end.status = "CONFIRMED"
            end.text = text
        else:
            dev.inputs.append(
                SignalEnd(
                    signal_id=signal_id,
                    direction="IN",
                    text=text,
                    status="CONFIRMED",
                )
            )

def recognize_pending_link_cross(project, origin_bay_id: str, origin_device_id: str, signal_id: str, dest_bay_id: str, dest_device_id: str) -> None:
    origin_bay = project.bays[origin_bay_id]
    dest_bay = project.bays[dest_bay_id]
    origin = origin_bay.devices[origin_device_id]
    dest = dest_bay.devices[dest_device_id]

    sig = origin_bay.signals.get(signal_id) or dest_bay.signals.get(signal_id)
    sig_name = sig.name if sig else signal_id
    sig_nature = sig.nature if sig else "DIGITAL"

    # ensure signal exists in both bays
    if signal_id not in origin_bay.signals:
        from domain.models import Signal
        origin_bay.signals[signal_id] = Signal(signal_id=signal_id, name=sig_name, nature=sig_nature)
    if signal_id not in dest_bay.signals:
        from domain.models import Signal
        dest_bay.signals[signal_id] = Signal(signal_id=signal_id, name=sig_name, nature=sig_nature)

    # update origin output text/status
    for e in origin.outputs:
        if e.signal_id == signal_id:
            left = sig_name
            if " hacia " in e.text:
                left, _ = e.text.split(" hacia ", 1)
                left = left.strip()
            e.text = f"{left} hacia {dest.name}"
            e.status = "CONFIRMED"
            break

    # Ensure destination IN exists AND is confirmed.
    # If the IN already exists (possibly pending), update it rather than returning.
    for e in dest.inputs:
        if e.signal_id == signal_id:
            left = sig_name
            if " desde " in e.text:
                left, _ = e.text.split(" desde ", 1)
                left = left.strip()
            e.text = f"{left} desde {origin.name}"
            e.status = "CONFIRMED"
            return

    from domain.models import SignalEnd
    dest.inputs.append(
        SignalEnd(
            signal_id=signal_id,
            direction="IN",
            text=f"{sig_name} desde {origin.name}",
            status="CONFIRMED",
        )
    )

def remove_link_project(project, signal_id: str) -> None:
    # remove endpoints in all bays/devices, and remove signal entry from each bay
    for bay in project.bays.values():
        for dev in bay.devices.values():
            dev.inputs[:] = [e for e in dev.inputs if e.signal_id != signal_id]
            dev.outputs[:] = [e for e in dev.outputs if e.signal_id != signal_id]
        bay.signals.pop(signal_id, None)
