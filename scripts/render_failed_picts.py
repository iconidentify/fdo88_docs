#!/usr/bin/env python3
"""
Render PICT files that ImageMagick and sips fail to convert.

Root causes found through binary analysis:

1. EMPTY PLACEHOLDERS (29 files, all GuideTool + IntrepidModule):
   512-byte zero header + 10 zero bytes. These are null PICT resources with
   no drawing commands, size field = 0, bounding box = (0,0,0,0). The AOL tool
   framework allocated PICT resource IDs but never populated them with image
   data. Nothing to render.

2. PICT V2 WITH CORRUPT HEADERS (5 files: SteveCase, SPiRaLTool, PandaTool):
   Valid PICT v2 data with PackBitsRect opcodes and 8-bit color tables, but
   the PICT header bounding box is either (0,0,0,0) or (-1,-1,W,H). The v2
   HeaderOp also has bogus resolution (0xFFFF0000 = 65535 dpi instead of 72)
   and corrupted srcRect. ImageMagick reads the bounding box first and bails
   when it sees zero/negative dimensions.
   Fix: Parse the clip region and PixMap bounds from the opcode stream, then
   patch the header fields.

3. PICT V1 WITH ZERO BOUNDING BOX (3 files: TOSTool):
   Valid PICT v1 with BitsRect opcode containing 32x32 1-bit bitmaps, but the
   header bounding box is (0,0,0,0). The actual coordinates are embedded in
   the clip region and bitmap bounds at offset coordinates like (211,214).
   Fix: Copy clip region rect into the header bounding box.

4. ADCR COMPRESSED (6 files, 3 unique: IPorts v1.1 Installer):
   Resource data starts with 'ADCR' magic - InstallerVISE (MindVision Software)
   proprietary compression. Format: ADCR(4) + method(1) + pad(1) + size(2).
   Method 0x03 is InstallerVISE's custom algorithm, not standard Mac Resource
   Manager dcmp compression (which uses 0xA89F6572 magic). No dcmp resource
   exists in the binary. Would require the InstallerVISE decompressor CODE
   resource or a classic Mac emulator with InstallerVISE installed.
   Cannot be rendered without the proprietary decompressor.

Usage:
    python3 render_failed_picts.py [art_directory]
"""

import struct
import subprocess
import os
import sys
import hashlib
import shutil
from pathlib import Path

DEFAULT_ART_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "site_data", "art"
)


def classify_pict(filepath):
    """Classify a PICT file by reading its binary structure."""
    with open(filepath, 'rb') as f:
        f.read(512)  # skip 512-byte zero header
        data = f.read()

    if len(data) <= 10:
        return 'empty', data

    if data[0:4] == b'ADCR':
        return 'adcr', data

    # Look for PICT v2 version opcode (0x0011 followed by 0x02FF)
    for i in range(10, min(len(data), 30)):
        if data[i:i+2] == b'\x00\x11' and i + 3 < len(data):
            if data[i+2:i+4] == b'\x02\xff':
                return 'pict_v2', data

    # Check for PICT v1 version (single-byte opcode 0x11, version 0x01)
    if len(data) > 11 and data[10] == 0x11 and data[11] == 0x01:
        return 'pict_v1', data

    return 'unknown', data


def fix_pict_v2(data):
    """Fix PICT v2 headers: bounding box, resolution, clip region.

    Returns fixed PICT file bytes (with 512-byte header) or (None, error).
    """
    mutable = bytearray(b'\x00' * 512 + data)

    clip_rect = None
    pixmap_rect = None

    pos = 512 + 10  # skip size(2) + bbox(8)
    while pos < len(mutable) - 4:
        op = struct.unpack('>H', mutable[pos:pos+2])[0]

        if op == 0x0011:  # Version
            pos += 4
        elif op == 0x0C00:  # HeaderOp
            pos += 26
        elif op == 0x0001:  # Clip region
            rgn_size = struct.unpack('>H', mutable[pos+2:pos+4])[0]
            clip_rect = struct.unpack('>hhhh', mutable[pos+4:pos+12])
            pos += 2 + rgn_size
        elif op == 0x001E:  # DefHilite
            pos += 2
        elif op in (0x0098, 0x0099, 0x0090, 0x0091):
            # PackBitsRect/Rgn or BitsRect/Rgn
            pm_start = pos + 2
            if pm_start + 10 <= len(mutable):
                pixmap_rect = struct.unpack('>hhhh', mutable[pm_start+2:pm_start+10])
            break
        elif op == 0x00FF:  # End
            break
        elif op == 0x00A0:  # ShortComment
            pos += 4
        elif op == 0x00A1:  # LongComment
            dlen = struct.unpack('>H', mutable[pos+4:pos+6])[0]
            pos += 6 + dlen
        elif op == 0x0007:  # PnSize
            pos += 6
        elif op == 0x0008:  # PnMode
            pos += 4
        elif op == 0x0009 or op == 0x000A:  # PnPat or FillPat
            pos += 10
        elif op == 0x0022:  # ShortLine
            pos += 8
        elif op == 0x0028:  # LongText
            tlen = mutable[pos+6]
            pos += 7 + tlen
            if pos % 2:
                pos += 1
        elif op == 0x0000:  # NOP
            pos += 2
        else:
            pos += 2

        if pos > 512 + 200:
            break

    # Determine correct bounding box from clip or pixmap
    if pixmap_rect:
        t, l, b, r = pixmap_rect
        w, h = r - l, b - t
        bbox = (0, 0, h, w)
    elif clip_rect:
        t, l, b, r = clip_rect
        if t < 0 or l < 0:
            w, h = r - l, b - t
            bbox = (0, 0, h, w)
        else:
            bbox = clip_rect
    else:
        return None, "No clip or pixmap rect found"

    # Patch bounding box
    struct.pack_into('>hhhh', mutable, 514, bbox[0], bbox[1], bbox[2], bbox[3])

    # Fix HeaderOp if present
    pos = 512 + 10
    while pos < len(mutable) - 4:
        op = struct.unpack('>H', mutable[pos:pos+2])[0]
        if op == 0x0011:
            pos += 4
        elif op == 0x0C00:
            hdr_off = pos + 2
            struct.pack_into('>h', mutable, hdr_off + 2, 0)  # reserved
            hres = struct.unpack('>I', mutable[hdr_off+4:hdr_off+8])[0]
            vres = struct.unpack('>I', mutable[hdr_off+8:hdr_off+12])[0]
            if hres == 0 or hres > 0x01000000:
                struct.pack_into('>I', mutable, hdr_off + 4, 0x00480000)  # 72 dpi
            if vres == 0 or vres > 0x01000000:
                struct.pack_into('>I', mutable, hdr_off + 8, 0x00480000)  # 72 dpi
            struct.pack_into('>hhhh', mutable, hdr_off + 12,
                             bbox[0], bbox[1], bbox[2], bbox[3])
            break
        else:
            break

    # Fix clip region negative coordinates
    pos = 512 + 10
    while pos < len(mutable) - 4:
        op = struct.unpack('>H', mutable[pos:pos+2])[0]
        if op == 0x0011:
            pos += 4
        elif op == 0x0C00:
            pos += 26
        elif op == 0x0001:
            old = struct.unpack('>hhhh', mutable[pos+4:pos+12])
            if old[0] < 0 or old[1] < 0:
                w, h = old[3] - old[1], old[2] - old[0]
                struct.pack_into('>hhhh', mutable, pos + 4, 0, 0, h, w)
            break
        else:
            break

    return bytes(mutable), None


def fix_pict_v1(data):
    """Fix PICT v1 headers: copy clip region rect into bounding box.

    Returns fixed PICT file bytes (with 512-byte header) or (None, error).
    """
    mutable = bytearray(b'\x00' * 512 + data)

    # PICT v1 opcode stream: version(2) at offset 10, then clip at 12
    if len(data) > 22 and data[12] == 0x01:  # clip opcode
        clip_rect = struct.unpack('>hhhh', data[15:23])
        struct.pack_into('>hhhh', mutable, 514,
                         clip_rect[0], clip_rect[1], clip_rect[2], clip_rect[3])
        return bytes(mutable), None

    return None, "No clip region found in v1 PICT"


def convert_with_magick(pict_bytes, output_path):
    """Write fixed PICT to temp file and convert with ImageMagick."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.pict', delete=False) as f:
        f.write(pict_bytes)
        tmp = f.name

    try:
        result = subprocess.run(
            ['magick', tmp, output_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and os.path.exists(output_path):
            if os.path.getsize(output_path) > 0:
                return True, None
            return False, "Output file is empty"
        return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp)


def main():
    art_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ART_DIR
    pict_files = sorted(Path(art_dir).rglob("*.pict"))

    if not pict_files:
        print(f"No .pict files found in {art_dir}")
        return

    rendered = []
    empty = []
    adcr = []
    failed = []
    duplicates = []
    seen = {}

    for pf in pict_files:
        with open(pf, 'rb') as f:
            content = f.read()
        md5 = hashlib.md5(content).hexdigest()

        category, data = classify_pict(str(pf))

        if category == 'empty':
            empty.append(str(pf))
            print(f"  EMPTY: {pf.name}")
            continue

        if category == 'adcr':
            target = struct.unpack('>H', data[6:8])[0]
            adcr.append(str(pf))
            print(f"  ADCR:  {pf.name} ({len(data)-8} -> {target} bytes)")
            continue

        if md5 in seen:
            duplicates.append((str(pf), seen[md5]))
            print(f"  DUPE:  {pf.name}")
            continue
        seen[md5] = str(pf)

        png_path = str(pf).replace('.pict', '.png')

        if category == 'pict_v2':
            fixed, err = fix_pict_v2(data)
        elif category == 'pict_v1':
            fixed, err = fix_pict_v1(data)
        else:
            failed.append((str(pf), f"Unknown format"))
            print(f"  FAIL:  {pf.name} (unknown format)")
            continue

        if err:
            failed.append((str(pf), err))
            print(f"  FAIL:  {pf.name} ({err})")
            continue

        ok, err = convert_with_magick(fixed, png_path)
        if ok:
            rendered.append(png_path)
            print(f"  OK:    {pf.name} -> {Path(png_path).name}")
        else:
            failed.append((str(pf), err))
            print(f"  FAIL:  {pf.name} ({err})")

    # Copy PNGs for duplicate PICTs
    for dup_path, orig_path in duplicates:
        orig_png = orig_path.replace('.pict', '.png')
        if os.path.exists(orig_png):
            dup_png = dup_path.replace('.pict', '.png')
            shutil.copy2(orig_png, dup_png)
            rendered.append(dup_png)
            print(f"  COPY:  {Path(dup_path).name} -> {Path(dup_png).name}")

    print(f"\n{'='*60}")
    print(f"Rendered:           {len(rendered)}")
    print(f"Empty placeholders: {len(empty)}")
    print(f"ADCR compressed:    {len(adcr)}")
    print(f"Duplicates:         {len(duplicates)}")
    print(f"Failed:             {len(failed)}")

    if failed:
        print(f"\nFailed:")
        for p, e in failed:
            print(f"  {Path(p).name}: {e}")


if __name__ == '__main__':
    main()
