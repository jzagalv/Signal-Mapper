from __future__ import annotations

def count_pending_for_bay(bay) -> dict:
    """Retorna conteos de pendientes para una bahía.
    Keys: in_pending, out_pending, total_pending
    """
    in_p = 0
    out_p = 0
    for dev in bay.devices.values():
        for e in dev.inputs:
            if (e.status or "").upper() == "PENDING":
                in_p += 1
        for e in dev.outputs:
            if (e.status or "").upper() == "PENDING":
                out_p += 1
    return {"in_pending": in_p, "out_pending": out_p, "total_pending": in_p + out_p}

def count_pending_for_device(dev) -> dict:
    in_p = sum(1 for e in dev.inputs if (e.status or "").upper() == "PENDING")
    out_p = sum(1 for e in dev.outputs if (e.status or "").upper() == "PENDING")
    return {"in_pending": in_p, "out_pending": out_p, "total_pending": in_p + out_p}
