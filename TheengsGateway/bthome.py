"""BTHome v2 support for Theengs Gateway.

Parses BTHome v2 service data (UUID 0xFCD2) into a dictionary of measurements.
"""
from __future__ import annotations

BTHOME_OBJECTS = {
    0x01: {"name": "batt", "kind": "number", "size": 1, "signed": False, "divisor": 1},
    0x02: {"name": "tempc", "kind": "number", "size": 2, "signed": True, "divisor": 100},
    0x03: {"name": "hum", "kind": "number", "size": 2, "signed": False, "divisor": 100},
    0x2E: {"name": "hum", "kind": "number", "size": 1, "signed": False, "divisor": 1},
    0x45: {"name": "tempc", "kind": "number", "size": 2, "signed": True, "divisor": 10},
    0x3A: {"name": "button", "kind": "button", "size": 1},
    0x53: {"name": "text", "kind": "text", "size": None},
    0x04: {"name": "pres", "kind": "number", "size": 3, "signed": False, "divisor": 100},
}


def parse_bthome_v2(servicedata_hex: str) -> dict | None:
    """Parse BTHome v2 service data."""
    try:
        data = bytes.fromhex(servicedata_hex)
    except ValueError:
        return
    # Empty data, or the lowest bit of the header is 1 (encrypted): don't parse.
    if len(data) == 0 or data[0] & 1:
        return
    # The top 3 bits of the header are the version; BTHome v2 is 010 (= 2).
    if (data[0] >> 5) != 2:
        return
    position = 1
    result = {}
    while position < len(data):
        object_id = data[position]
        # .get() returns None for an unknown ID instead of raising KeyError.
        spec = BTHOME_OBJECTS.get(object_id)
        if spec is None:
            break
        if spec["kind"] == "text":
            if position + 1 >= len(data):
                return None
            value_size = data[position + 1]
            value_start = position + 2
        else:
            value_size = spec["size"]
            value_start = position + 1

        value_end = value_start + value_size
        if value_end > len(data):
            return
        value_bytes = data[value_start:value_end]
        if spec["kind"] == "button":
            if value_bytes[0] == 1:
                value = "press"
            elif value_bytes[0] == 2:
                value = "double_press"
            else:
                value = value_bytes[0]
        elif spec["kind"] == "text":
            try:
                value = value_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return None
        else:
            value = int.from_bytes(
                value_bytes, "little", signed=spec["signed"]
            ) / spec["divisor"]

        name = spec["name"]
        # If the name is already taken, add a suffix (_2, _3, ...) so that
        # a second measurement of the same kind doesn't overwrite the first.
        if name in result:
            number = 2
            while f"{name}_{number}" in result:
                number += 1
            name = f"{name}_{number}"

        result[name] = value
        position = value_end
    if not result:
        return None
    return result

