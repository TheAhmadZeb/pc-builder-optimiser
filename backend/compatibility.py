from __future__ import annotations

from typing import Any


def _parse_pcie_version(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().upper()
    text = text.replace('PCI-E', 'PCIE')
    text = text.replace('PCIe', 'PCIE')
    text = text.replace('PCI', '')
    text = text.replace('PCIE', '')
    text = text.replace('GEN', '')
    text = text.replace('X', '')
    text = text.replace(' ', '')

    filtered = ''.join(ch for ch in text if ch.isdigit() or ch == '.')
    if not filtered:
        return 0.0

    try:
        return float(filtered)
    except ValueError:
        return 0.0


def check_compatibility(
    cpu: dict[str, Any],
    gpu: dict[str, Any],
    motherboard: dict[str, Any],
    ram: dict[str, Any],
    psu: dict[str, Any],
    total_power: int,
) -> tuple[bool, str]:
    compatible = True
    message = ''

    if cpu['Socket_Type'] != motherboard['Socket_Type']:
        return False, 'CPU socket incompatible with motherboard'

    if ram['RAM_Type'] != motherboard['RAM_Type']:
        return False, 'RAM type incompatible with motherboard'

    if psu['Wattage'] < total_power:
        return False, 'PSU wattage insufficient'

    gpu_pcie = _parse_pcie_version(gpu['PCIE_Version'])
    motherboard_pcie = _parse_pcie_version(motherboard['PCIE_Version'])
    if gpu_pcie > motherboard_pcie:
        message = 'GPU PCIe version higher than supported by motherboard'

    return compatible, message