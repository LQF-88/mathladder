#!/usr/bin/env python3
"""Verify that native libraries in an APK/AAB support 16 KB memory pages.

Android 15+ devices may use 16 KB pages instead of 4 KB. For the app to
launch on those devices every 64-bit native library must have its ELF
``PT_LOAD`` segments aligned to at least 16 KB, and uncompressed libraries
must also start at a 16 KB-aligned offset inside the zip container.

Usage:
    python tools/check_apk_alignment.py bin/*.apk
    python tools/check_apk_alignment.py bin/*.aab

Exits with status 1 when a 64-bit library is not compatible.
"""

from __future__ import annotations

import struct
import sys
import zipfile
from pathlib import Path

PAGE_SIZE_16K = 16 * 1024
PT_LOAD = 1
KNOWN_ABIS = {
    "arm64-v8a",
    "armeabi-v7a",
    "x86",
    "x86_64",
    "riscv64",
    "mips",
    "mips64",
}
BITNESS_64 = {"arm64-v8a", "x86_64", "mips64", "riscv64"}


def native_library(name: str) -> tuple[str, str] | None:
    """Return ``(abi, filename)`` for a zip entry that is a native library."""
    if not name.endswith(".so"):
        return None
    parts = name.split("/")
    for index in range(len(parts) - 2):
        if parts[index] == "lib" and parts[index + 1] in KNOWN_ABIS:
            return parts[index + 1], parts[-1]
    return None


def load_segment_alignments(blob: bytes) -> list[int]:
    """Return the ``p_align`` values of every ELF ``PT_LOAD`` segment."""
    if len(blob) < 64 or blob[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")
    elf_class = blob[4]
    endian = "<" if blob[5] == 1 else ">"
    if elf_class == 2:  # ELF64
        phoff = struct.unpack_from(endian + "Q", blob, 0x20)[0]
        phentsize = struct.unpack_from(endian + "H", blob, 0x36)[0]
        phnum = struct.unpack_from(endian + "H", blob, 0x38)[0]
        align_format, align_offset = endian + "Q", 48
    elif elf_class == 1:  # ELF32
        phoff = struct.unpack_from(endian + "I", blob, 0x1C)[0]
        phentsize = struct.unpack_from(endian + "H", blob, 0x2A)[0]
        phnum = struct.unpack_from(endian + "H", blob, 0x2C)[0]
        align_format, align_offset = endian + "I", 28
    else:
        raise ValueError(f"unsupported ELF class {elf_class}")

    aligns: list[int] = []
    for index in range(phnum):
        base = phoff + index * phentsize
        if base + align_offset + struct.calcsize(align_format) > len(blob):
            raise ValueError("truncated ELF program header table")
        p_type = struct.unpack_from(endian + "I", blob, base)[0]
        if p_type == PT_LOAD:
            aligns.append(struct.unpack_from(align_format, blob, base + align_offset)[0])
    return aligns


def stored_data_offset(handle, info: zipfile.ZipInfo) -> int | None:
    """Return the file offset of a zip entry's payload (stored entries only)."""
    handle.seek(info.header_offset)
    header = handle.read(30)
    if len(header) < 30 or header[:4] != b"PK\x03\x04":
        return None
    name_length, extra_length = struct.unpack_from("<HH", header, 26)
    return info.header_offset + 30 + name_length + extra_length


def check_archive(path: Path) -> bool:
    print(f"检查 {path}")
    ok = True
    found = 0
    with zipfile.ZipFile(path) as archive, path.open("rb") as handle:
        for info in archive.infolist():
            native = native_library(info.filename)
            if native is None:
                continue
            abi, filename = native
            found += 1
            try:
                aligns = load_segment_alignments(archive.read(info))
            except ValueError as exc:
                print(f"  [错误] {abi:12} {filename:28} {exc}")
                ok = False
                continue

            min_align = min(aligns) if aligns else 0
            required = PAGE_SIZE_16K if abi in BITNESS_64 else 4096
            elf_ok = min_align >= required
            detail = f"{min_align}"
            if info.compress_type == zipfile.ZIP_STORED:
                data_offset = stored_data_offset(handle, info)
                zip_ok = data_offset is not None and data_offset % PAGE_SIZE_16K == 0
                zip_state = "对齐" if zip_ok else "未对齐"
                detail += f"  ZIP {data_offset} ({zip_state})"
            else:
                zip_ok = True
                zip_state = "压缩存储"
                detail += f"  ZIP {zip_state}"

            if not elf_ok or not zip_ok:
                ok = False
                print(f"  [失败] {abi:12} {filename:28} {detail}")
            else:
                print(f"  [通过] {abi:12} {filename:28} {detail}")

    if not found:
        print("  [错误] 压缩包中没有找到原生库")
        return False
    print("  结果:", "通过" if ok else "失败")
    return ok


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip())
        return 2
    results = [check_archive(Path(argument)) for argument in argv]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
