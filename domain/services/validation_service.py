from __future__ import annotations

def validate_signal(bay, signal_id: str):
    ins, outs = [], []
    for dev in bay.devices.values():
        ins += [e for e in dev.inputs if e.signal_id == signal_id]
        outs += [e for e in dev.outputs if e.signal_id == signal_id]

    issues = []
    if outs and not ins:
        if all(getattr(o, "status", "CONFIRMED") == "PENDING" for o in outs):
            issues.append(("WARNING", "Salida pendiente sin entrada espejo (aún no reconocida)"))
        else:
            issues.append(("WARNING", "Salida sin entrada asociada"))
    if ins and not outs:
        issues.append(("ERROR", "Entrada sin salida asociada (inconsistencia)"))

    for dev in bay.devices.values():
        di = [e.signal_id for e in dev.inputs]
        do = [e.signal_id for e in dev.outputs]
        if len(di) != len(set(di)):
            issues.append(("ERROR", f"Duplicado en entradas de {dev.name}"))
        if len(do) != len(set(do)):
            issues.append(("ERROR", f"Duplicado en salidas de {dev.name}"))
    return issues

def validate_bay(bay):
    issues = []
    for dev in bay.devices.values():
        for e in dev.inputs + dev.outputs:
            if getattr(e, "status", "CONFIRMED") == "PENDING":
                issues.append(("WARNING", f"Pendiente: {dev.name} ({e.direction}) -> {e.text}"))
    signal_ids=set()
    for dev in bay.devices.values():
        for e in dev.inputs + dev.outputs:
            signal_ids.add(e.signal_id)
    for sid in sorted(signal_ids):
        issues.extend([(lvl, f"{sid}: {msg}") for (lvl,msg) in validate_signal(bay, sid)])
    return issues
