"""A minimal protobuf wire-format reader: enough for Anki's package `meta`, its media map and
the schema-18 config blobs (note types, templates, decks, deck options). The input is
untrusted, so every read is bounds-checked and anything odd raises ProtoError."""

import struct

type Fields = dict[int, list[int | bytes]]


class ProtoError(ValueError):
    pass


def _varint(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    for shift in range(0, 70, 7):
        if pos >= len(data):
            raise ProtoError("truncated varint")
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
    raise ProtoError("varint too long")


def decode(data: bytes) -> Fields:
    """{field number: [values]}: varints and fixed-width values as ints, everything
    length-delimited (strings, bytes, messages, packed arrays) as bytes."""
    out: Fields = {}
    pos = 0
    while pos < len(data):
        key, pos = _varint(data, pos)
        number, wire = key >> 3, key & 7
        if number == 0:
            raise ProtoError("field number 0")
        value: int | bytes
        if wire == 0:
            value, pos = _varint(data, pos)
        elif wire in (1, 5):
            size = 8 if wire == 1 else 4
            if pos + size > len(data):
                raise ProtoError("truncated fixed-width field")
            value = int.from_bytes(data[pos : pos + size], "little")
            pos += size
        elif wire == 2:
            length, pos = _varint(data, pos)
            if pos + length > len(data):
                raise ProtoError("truncated length-delimited field")
            value = bytes(data[pos : pos + length])
            pos += length
        else:
            raise ProtoError(f"unsupported wire type {wire}")
        out.setdefault(number, []).append(value)
    return out


def integer(fields: Fields, number: int, default: int = 0) -> int:
    values = [v for v in fields.get(number, []) if isinstance(v, int)]
    return values[-1] if values else default


def signed(fields: Fields, number: int, default: int = 0) -> int:
    """An int32/int64 field (two's complement in a varint)."""
    value = integer(fields, number, default)
    return value - (1 << 64) if value >= 1 << 63 else value


def raw(fields: Fields, number: int) -> bytes | None:
    values = [v for v in fields.get(number, []) if isinstance(v, bytes)]
    return values[-1] if values else None


def text(fields: Fields, number: int, default: str = "") -> str:
    value = raw(fields, number)
    if value is None:
        return default
    try:
        return value.decode()
    except UnicodeDecodeError as exc:
        raise ProtoError(f"field {number} is not UTF-8") from exc


def message(fields: Fields, number: int) -> Fields | None:
    value = raw(fields, number)
    return None if value is None else decode(value)


def messages(fields: Fields, number: int) -> list[Fields]:
    return [decode(v) for v in fields.get(number, []) if isinstance(v, bytes)]


def _f32(bits: int) -> float:
    """A float32 as the shortest decimal that reads back to it (0.9, not 0.89999997...)."""
    value = float(struct.unpack("<f", (bits & 0xFFFFFFFF).to_bytes(4, "little"))[0])
    return float(f"{value:.7g}")


def float32(fields: Fields, number: int) -> float | None:
    values = [v for v in fields.get(number, []) if isinstance(v, int)]
    return _f32(values[-1]) if values else None


def floats(fields: Fields, number: int) -> list[float]:
    """A repeated float field, packed (the proto3 default) or not."""
    out: list[float] = []
    for value in fields.get(number, []):
        if isinstance(value, bytes):
            if len(value) % 4:
                raise ProtoError(f"packed floats in field {number} have a bad length")
            out += [_f32(b) for b in struct.unpack(f"<{len(value) // 4}I", value)]
        else:
            out.append(_f32(value))
    return out
