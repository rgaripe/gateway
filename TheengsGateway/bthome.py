"""BTHome v2 support for Theengs Gateway.

Parses BTHome v2 service data (UUID 0xFCD2) into a dictionary of measurements.
Object IDs and their formats follow https://bthome.io/format/
"""
from __future__ import annotations

from decimal import Decimal


def _number(name: str, size: int, signed: bool = False, factor: float = 1) -> dict:
    """Passport of a numeric object: an integer of `size` bytes times `factor`."""
    return {"name": name, "kind": "number", "size": size, "signed": signed, "factor": factor}


def _binary(name: str) -> dict:
    """Passport of a binary sensor: one byte, 0 = False, 1 = True."""
    return {"name": name, "kind": "binary", "size": 1}


BUTTON_EVENTS = {
    0x01: "press",
    0x02: "double_press",
    0x03: "triple_press",
    0x04: "long_press",
    0x05: "long_double_press",
    0x06: "long_triple_press",
    0x80: "hold_press",
    0x81: "hold_release",
}

DIMMER_EVENTS = {
    0x01: "rotate_left",
    0x02: "rotate_right",
}

LIGHT_LEVELS = {
    0x00: "dark",
    0x01: "twilight",
    0x02: "bright",
}

BTHOME_OBJECTS = {
    # Misc
    0x00: _number("packet_id", 1),
    # Sensor data
    0x01: _number("batt", 1),
    0x02: _number("tempc", 2, signed=True, factor=0.01),
    0x03: _number("hum", 2, factor=0.01),
    0x04: _number("pres", 3, factor=0.01),
    0x05: _number("lux", 3, factor=0.01),
    0x06: _number("mass_kg", 2, factor=0.01),
    0x07: _number("mass_lb", 2, factor=0.01),
    0x08: _number("dewpointc", 2, signed=True, factor=0.01),
    0x09: _number("count", 1),
    0x0A: _number("energy", 3, factor=0.001),
    0x0B: _number("power", 3, factor=0.01),
    0x0C: _number("volt", 2, factor=0.001),
    0x0D: _number("pm25", 2),
    0x0E: _number("pm10", 2),
    # Binary sensors
    0x0F: _binary("generic_boolean"),
    0x10: _binary("power_on"),
    0x11: _binary("open"),
    # Sensor data
    0x12: _number("co2", 2),
    0x13: _number("tvoc", 2),
    0x14: _number("moi", 2, factor=0.01),
    # Binary sensors
    0x15: _binary("batt_low"),
    0x16: _binary("batt_charging"),
    0x17: _binary("carbon_monoxide"),
    0x18: _binary("cold"),
    0x19: _binary("connected"),
    0x1A: _binary("door_open"),
    0x1B: _binary("garage_door_open"),
    0x1C: _binary("gas_detected"),
    0x1D: _binary("heat"),
    0x1E: _binary("light"),
    0x1F: _binary("unlocked"),
    0x20: _binary("wet"),
    0x21: _binary("motion"),
    0x22: _binary("moving"),
    0x23: _binary("occupancy"),
    0x24: _binary("plugged_in"),
    0x25: _binary("presence"),
    0x26: _binary("problem"),
    0x27: _binary("running"),
    0x28: _binary("safe"),
    0x29: _binary("smoke"),
    0x2A: _binary("sound"),
    0x2B: _binary("tamper"),
    0x2C: _binary("vibration"),
    0x2D: _binary("window_open"),
    # Sensor data
    0x2E: _number("hum", 1),
    0x2F: _number("moi", 1),
    # Events
    0x3A: {"name": "button", "kind": "event", "size": 1, "events": BUTTON_EVENTS},
    # 0x3B (command) is not supported yet: the examples in the specification
    # have different lengths (3B0000 vs 3B010305), so its size is unclear.
    0x3C: {"name": "dimmer", "kind": "dimmer", "size": 2, "events": DIMMER_EVENTS},
    # Sensor data
    0x3D: _number("count", 2),
    0x3E: _number("count", 4),
    0x3F: _number("rotation", 2, signed=True, factor=0.1),
    0x40: _number("distance_mm", 2),
    0x41: _number("distance_m", 2, factor=0.1),
    0x42: _number("duration", 3, factor=0.001),
    0x43: _number("current", 2, factor=0.001),
    0x44: _number("speed", 2, factor=0.01),
    0x45: _number("tempc", 2, signed=True, factor=0.1),
    0x46: _number("uv_index", 1, factor=0.1),
    0x47: _number("volume_l", 2, factor=0.1),
    0x48: _number("volume_ml", 2),
    0x49: _number("volume_flow_rate", 2, factor=0.001),
    0x4A: _number("volt", 2, factor=0.1),
    0x4B: _number("gas", 3, factor=0.001),
    0x4C: _number("gas", 4, factor=0.001),
    0x4D: _number("energy", 4, factor=0.001),
    0x4E: _number("volume_l", 4, factor=0.001),
    0x4F: _number("water", 4, factor=0.001),
    0x50: _number("timestamp", 4),
    0x51: _number("accel", 2, factor=0.001),
    0x52: _number("gyro", 2, factor=0.001),
    # Variable length: the length is in the byte after the object ID.
    0x53: {"name": "text", "kind": "text", "size": None},
    0x54: {"name": "raw", "kind": "raw", "size": None},
    # Sensor data
    0x55: _number("volume_storage", 4, factor=0.001),
    0x56: _number("conductivity", 2),
    0x57: _number("tempc", 1, signed=True),
    0x58: _number("tempc", 1, signed=True, factor=0.35),
    0x59: _number("count", 1, signed=True),
    0x5A: _number("count", 2, signed=True),
    0x5B: _number("count", 4, signed=True),
    0x5C: _number("power", 4, signed=True, factor=0.01),
    0x5D: _number("current", 2, signed=True, factor=0.001),
    0x5E: _number("direction", 2, factor=0.01),
    0x5F: _number("precipitation", 2, factor=0.1),
    0x60: _number("channel", 1),
    0x61: _number("rotational_speed", 2),
    0x62: _number("speed", 4, signed=True, factor=0.000001),
    0x63: _number("accel", 4, signed=True, factor=0.000001),
    0x64: {"name": "light_level", "kind": "event", "size": 1, "events": LIGHT_LEVELS},
    0x65: _number("settings_revision", 1),
    # Device information
    0xF0: _number("device_type_id", 2),
    0xF1: {"name": "firmware_version", "kind": "version", "size": 4},
    0xF2: {"name": "firmware_version", "kind": "version", "size": 3},
}


def read_number(spec: dict, value_bytes: bytes) -> int | float:
    """Read a little-endian integer and multiply it by the factor."""
    raw = int.from_bytes(value_bytes, "little", signed=spec["signed"])
    factor = spec["factor"]
    if factor == 1:
        # Keep whole numbers whole: 97, not 97.0.
        return raw
    # Round to as many decimals as the factor has (0.01 -> 2, 0.35 -> 2,
    # 0.000001 -> 6), otherwise float math gives e.g. 50.550000000000004.
    decimals = -Decimal(str(factor)).as_tuple().exponent
    return round(raw * factor, decimals)


def read_event(spec: dict, value_bytes: bytes) -> str | int:
    """Translate an event code into its name, or return the code if unknown."""
    return spec["events"].get(value_bytes[0], value_bytes[0])


def read_dimmer(spec: dict, value_bytes: bytes) -> dict:
    """Read a dimmer event: first byte is the event, second the number of steps."""
    code = value_bytes[0]
    return {"event": spec["events"].get(code, code), "steps": value_bytes[1]}


def read_binary(spec: dict, value_bytes: bytes) -> bool:
    """Read a binary sensor: 0 is False, anything else is True."""
    return value_bytes[0] != 0


def read_version(spec: dict, value_bytes: bytes) -> str:
    """Read a firmware version, most significant part last: 00 01 02 04 -> 4.2.1.0."""
    return ".".join(str(part) for part in reversed(value_bytes))


def read_text(spec: dict, value_bytes: bytes) -> str:
    """Decode the text from the value bytes."""
    return value_bytes.decode("utf-8")


def read_raw(spec: dict, value_bytes: bytes) -> str:
    """Return the raw bytes as a hex string."""
    return value_bytes.hex()


READERS = {
    "number": read_number,
    "event": read_event,
    "dimmer": read_dimmer,
    "binary": read_binary,
    "version": read_version,
    "text": read_text,
    "raw": read_raw,
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
        if spec["size"] is None:
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
        # Pick the reader function for this kind of object and call it.
        reader = READERS[spec["kind"]]
        try:
            value = reader(spec, value_bytes)
        except UnicodeDecodeError:
            return None

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
