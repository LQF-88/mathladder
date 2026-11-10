"""Tests for the APK 16 KB page-size checker."""

from __future__ import annotations

import struct

import pytest

from tools.check_apk_alignment import load_segment_alignments, native_library


def elf64(align: int) -> bytes:
    blob = bytearray(64 + 56)
    blob[:4] = b"\x7fELF"
    blob[4] = 2
    blob[5] = 1
    struct.pack_into("<Q", blob, 0x20, 64)
    struct.pack_into("<H", blob, 0x36, 56)
    struct.pack_into("<H", blob, 0x38, 1)
    struct.pack_into("<I", blob, 64, 1)  # PT_LOAD
    struct.pack_into("<Q", blob, 64 + 48, align)
    return bytes(blob)


def elf32(align: int) -> bytes:
    blob = bytearray(52 + 32)
    blob[:4] = b"\x7fELF"
    blob[4] = 1
    blob[5] = 1
    struct.pack_into("<I", blob, 0x1C, 52)
    struct.pack_into("<H", blob, 0x2A, 32)
    struct.pack_into("<H", blob, 0x2C, 1)
    struct.pack_into("<I", blob, 52, 1)  # PT_LOAD
    struct.pack_into("<I", blob, 52 + 28, align)
    return bytes(blob)


def test_elf64_load_alignment() -> None:
    assert load_segment_alignments(elf64(16384)) == [16384]
    assert load_segment_alignments(elf64(4096)) == [4096]


def test_elf32_load_alignment() -> None:
    assert load_segment_alignments(elf32(4096)) == [4096]


def test_truncated_program_headers_raise() -> None:
    blob = bytearray(elf64(16384))
    struct.pack_into("<H", blob, 0x38, 10)
    with pytest.raises(ValueError, match="truncated"):
        load_segment_alignments(bytes(blob))


def test_native_library_paths() -> None:
    assert native_library("lib/arm64-v8a/libpython3.11.so") == (
        "arm64-v8a",
        "libpython3.11.so",
    )
    assert native_library("base/lib/armeabi-v7a/libSDL2.so") == (
        "armeabi-v7a",
        "libSDL2.so",
    )
    assert native_library("base/assets/fonts/NotoSansSC-Regular.otf") is None
    assert native_library("lib/unknown-abi/libfoo.so") is None
    assert native_library("classes.dex") is None
