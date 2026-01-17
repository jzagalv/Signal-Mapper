from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

Nature = Literal["DIGITAL", "ANALOG"]
Direction = Literal["IN", "OUT"]
LinkStatus = Literal["CONFIRMED", "PENDING"]
InterlockMode = Literal["AND", "OR"]


@dataclass
class Signal:
    signal_id: str
    name: str
    nature: Nature = "DIGITAL"
    description: str = ""


@dataclass
class InterlockItem:
    """Un enclavamiento (bloqueo) aplicado a una entrada.

    relay_tag: Tag del relé que bloquea (OBLIGATORIO, p.ej. '86T2').
    source_device_id/source_signal_id son opcionales (preparado para futura navegación/diagrama lógico).
    """

    relay_tag: str
    category: str = "Bloqueos"
    source_device_id: Optional[str] = None
    source_signal_id: Optional[str] = None


@dataclass
class InterlockSpec:
    mode: InterlockMode = "AND"  # hoy: AND (serie). Futuro: OR (paralelo)
    items: List[InterlockItem] = field(default_factory=list)


@dataclass
class SignalEnd:
    signal_id: str
    direction: Direction
    text: str
    status: LinkStatus = "CONFIRMED"
    test_block: bool = False  # sólo aplica normalmente a OUT
    interlocks: Optional[InterlockSpec] = None  # sólo aplica normalmente a IN


@dataclass
class Device:
    device_id: str
    bay_id: str
    name: str
    dev_type: str = "IED"
    inputs: List[SignalEnd] = field(default_factory=list)
    outputs: List[SignalEnd] = field(default_factory=list)


@dataclass
class Bay:
    bay_id: str
    name: str
    devices: Dict[str, Device] = field(default_factory=dict)
    signals: Dict[str, Signal] = field(default_factory=dict)


@dataclass
class CanvasLayout:
    bay_id: str
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    device_positions: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class SignalTemplate:
    code: str
    label: str
    nature: Nature = "DIGITAL"
    category: str = "General"
    description: str = ""


@dataclass
class Project:
    schema_version: str
    name: str
    bays: Dict[str, Bay] = field(default_factory=dict)
    canvases: Dict[str, CanvasLayout] = field(default_factory=dict)
    templates: List[SignalTemplate] = field(default_factory=list)
