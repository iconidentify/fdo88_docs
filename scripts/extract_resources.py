#!/usr/bin/env python3
"""
Classic Macintosh Resource Fork Extractor for AOL Tool Binaries
===============================================================

Extracts art (PICT, ICN#, icl4, icl8, ics#, ics4, ics8, cicn, ICON, CURS),
sounds (snd), text (TEXT, STR, STR#), FDO88 forms (DB*), and metadata (vers, Tinf)
from classic Mac resource forks preserved in extracted StuffIt archives.

Requires: macOS (for resource fork access via ..namedfork/rsrc), Python 3.9+
Optional: Pillow (for icon-to-PNG conversion), ffmpeg (for snd-to-WAV)

Usage:
    python3 extract_resources.py <extracted_tools_dir> <output_dir>
    python3 extract_resources.py ../extracted_tools ../site_data
"""

import os
import sys
import json
import struct
import subprocess
import shutil
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Resource Fork Parser
# ---------------------------------------------------------------------------

def parse_resource_fork(rsrc_data):
    """Parse a Macintosh resource fork into individual resources.

    Resource fork structure:
      Header (16 bytes):
        offset 0:  uint32 - offset to resource data
        offset 4:  uint32 - offset to resource map
        offset 8:  uint32 - length of resource data
        offset 12: uint32 - length of resource map

      Resource Data section:
        Each entry: uint32 length prefix, then raw data bytes

      Resource Map:
        offset+0:   16 bytes reserved (copy of header)
        offset+16:  4 bytes reserved
        offset+20:  2 bytes reserved
        offset+22:  2 bytes file attributes
        offset+24:  uint16 offset to type list (from map start)
        offset+26:  uint16 offset to name list (from map start)

      Type List (at map + type_list_offset):
        uint16: count - 1 (number of types minus one)
        For each type:
          4 bytes: resource type (e.g. 'PICT')
          uint16:  count - 1 (number of resources of this type minus one)
          uint16:  offset to reference list (from type list start)

      Reference List (for each resource):
        uint16: resource ID
        uint16: offset to name (from name list start), or 0xFFFF if none
        uint8:  resource attributes
        uint24: offset to data (from resource data start)
        uint32: reserved (handle)
    """
    if len(rsrc_data) < 16:
        return []

    data_offset, map_offset, data_len, map_len = struct.unpack('>IIII', rsrc_data[:16])

    if map_offset + map_len > len(rsrc_data) or data_offset + data_len > len(rsrc_data):
        return []

    resource_map = rsrc_data[map_offset:]
    if len(resource_map) < 28:
        return []

    type_list_off = struct.unpack('>H', resource_map[24:26])[0]
    name_list_off = struct.unpack('>H', resource_map[26:28])[0]

    type_list = resource_map[type_list_off:]
    if len(type_list) < 2:
        return []

    num_types = struct.unpack('>H', type_list[:2])[0] + 1

    resources = []

    for i in range(num_types):
        entry_offset = 2 + i * 8
        if entry_offset + 8 > len(type_list):
            break

        res_type = type_list[entry_offset:entry_offset+4]
        num_resources = struct.unpack('>H', type_list[entry_offset+4:entry_offset+6])[0] + 1
        ref_list_off = struct.unpack('>H', type_list[entry_offset+6:entry_offset+8])[0]

        ref_list = type_list[ref_list_off:]

        for j in range(num_resources):
            ref_offset = j * 12
            if ref_offset + 12 > len(ref_list):
                break

            res_id = struct.unpack('>h', ref_list[ref_offset:ref_offset+2])[0]
            name_off = struct.unpack('>H', ref_list[ref_offset+2:ref_offset+4])[0]
            attrs = ref_list[ref_offset+4]
            data_off_bytes = ref_list[ref_offset+5:ref_offset+8]
            res_data_offset = (data_off_bytes[0] << 16) | (data_off_bytes[1] << 8) | data_off_bytes[2]

            # Get resource name
            res_name = None
            if name_off != 0xFFFF:
                name_data = resource_map[name_list_off + name_off:]
                if len(name_data) > 0:
                    name_len = name_data[0]
                    if len(name_data) > name_len:
                        res_name = name_data[1:1+name_len].decode('mac_roman', errors='replace')

            # Get resource data
            abs_data_offset = data_offset + res_data_offset
            if abs_data_offset + 4 <= len(rsrc_data):
                res_len = struct.unpack('>I', rsrc_data[abs_data_offset:abs_data_offset+4])[0]
                res_data = rsrc_data[abs_data_offset+4:abs_data_offset+4+res_len]
            else:
                res_data = b''

            try:
                type_str = res_type.decode('mac_roman')
            except:
                type_str = res_type.hex()

            resources.append({
                'type': type_str,
                'id': res_id,
                'name': res_name,
                'attrs': attrs,
                'data': res_data,
                'size': len(res_data)
            })

    return resources


def read_resource_fork(filepath):
    """Read the resource fork of a file (macOS only)."""
    rsrc_path = filepath + '/..namedfork/rsrc'
    try:
        with open(rsrc_path, 'rb') as f:
            return f.read()
    except (FileNotFoundError, PermissionError):
        return None


# ---------------------------------------------------------------------------
# Icon Converters (ICN#, icl4, icl8, ics#, ics4, ics8 -> PNG)
# ---------------------------------------------------------------------------

def icon_1bit_to_pixels(data, size):
    """Convert 1-bit icon data to RGBA pixel array."""
    pixels = []
    byte_width = size // 8
    # data contains icon bitmap followed by mask bitmap
    icon_bytes = data[:byte_width * size]
    mask_bytes = data[byte_width * size:byte_width * size * 2] if len(data) >= byte_width * size * 2 else None

    for y in range(size):
        for x in range(size):
            byte_idx = y * byte_width + x // 8
            bit_idx = 7 - (x % 8)

            if byte_idx < len(icon_bytes):
                pixel = (icon_bytes[byte_idx] >> bit_idx) & 1
            else:
                pixel = 0

            if mask_bytes and byte_idx < len(mask_bytes):
                mask = (mask_bytes[byte_idx] >> bit_idx) & 1
            else:
                mask = 1

            if mask:
                color = (0, 0, 0, 255) if pixel else (255, 255, 255, 255)
            else:
                color = (0, 0, 0, 0)
            pixels.append(color)

    return pixels


# Classic Mac 4-bit color table
CLUT4 = [
    (255,255,255), (252,243,5), (255,100,2), (221,8,6),
    (240,2,159), (70,0,165), (0,0,211), (2,170,234),
    (0,187,0), (0,100,17), (86,44,5), (144,113,58),
    (192,192,192), (128,128,128), (64,64,64), (0,0,0)
]

# Classic Mac 8-bit color table (simplified - standard Mac 256-color palette)
def make_clut8():
    """Generate the standard Macintosh 8-bit color lookup table."""
    table = []
    # The Mac 256-color palette: 6x6x6 color cube + ramps
    for i in range(256):
        if i == 0:
            table.append((255, 255, 255))
        elif i == 255:
            table.append((0, 0, 0))
        else:
            # Approximate the standard Mac palette
            r_steps = [0xFF, 0xFC, 0xF2, 0xD6, 0xB3, 0x90, 0x6C, 0x48, 0x24, 0x00]
            g_steps = [0xFF, 0xFC, 0xF2, 0xD6, 0xB3, 0x90, 0x6C, 0x48, 0x24, 0x00]
            b_steps = [0xFF, 0xFC, 0xF2, 0xD6, 0xB3, 0x90, 0x6C, 0x48, 0x24, 0x00]

            # Standard 6x6x6 cube mapping
            idx = i - 1
            if idx < 215:
                r = idx // 36
                g = (idx % 36) // 6
                b = idx % 6
                table.append((255 - r * 51, 255 - g * 51, 255 - b * 51))
            else:
                # Grayscale ramp for remaining entries
                gray = 255 - ((idx - 215) * 255 // 40)
                gray = max(0, min(255, gray))
                table.append((gray, gray, gray))
    return table

CLUT8 = make_clut8()


def icon_4bit_to_pixels(data, size):
    """Convert 4-bit icon to RGBA pixels."""
    pixels = []
    for y in range(size):
        for x in range(size):
            byte_idx = (y * size + x) // 2
            if byte_idx < len(data):
                byte = data[byte_idx]
                if x % 2 == 0:
                    idx = (byte >> 4) & 0x0F
                else:
                    idx = byte & 0x0F
                r, g, b = CLUT4[idx]
                pixels.append((r, g, b, 255))
            else:
                pixels.append((0, 0, 0, 0))
    return pixels


def icon_8bit_to_pixels(data, size):
    """Convert 8-bit icon to RGBA pixels."""
    pixels = []
    for y in range(size):
        for x in range(size):
            idx = y * size + x
            if idx < len(data):
                color_idx = data[idx]
                r, g, b = CLUT8[color_idx]
                pixels.append((r, g, b, 255))
            else:
                pixels.append((0, 0, 0, 0))
    return pixels


def save_icon_as_png(pixels, size, output_path):
    """Save pixel array as PNG using Pillow."""
    try:
        from PIL import Image
        img = Image.new('RGBA', (size, size))
        img.putdata(pixels)
        # Scale up small icons for visibility
        if size <= 16:
            img = img.resize((64, 64), Image.NEAREST)
        elif size <= 32:
            img = img.resize((128, 128), Image.NEAREST)
        img.save(output_path, 'PNG')
        return True
    except Exception as e:
        print(f"    Warning: PNG save failed: {e}")
        return False


def extract_icon(resource, output_dir, tool_name):
    """Extract an icon resource to PNG."""
    res_type = resource['type']
    res_id = resource['id']
    data = resource['data']

    safe_name = tool_name.replace('/', '_').replace(' ', '_')
    filename = f"{safe_name}_{res_type.strip()}_{res_id}.png"
    output_path = os.path.join(output_dir, filename)

    try:
        if res_type == 'ICN#':
            # 32x32 1-bit with mask (128 bytes icon + 128 bytes mask)
            pixels = icon_1bit_to_pixels(data, 32)
            return save_icon_as_png(pixels, 32, output_path), output_path
        elif res_type == 'icl4':
            pixels = icon_4bit_to_pixels(data, 32)
            return save_icon_as_png(pixels, 32, output_path), output_path
        elif res_type == 'icl8':
            pixels = icon_8bit_to_pixels(data, 32)
            return save_icon_as_png(pixels, 32, output_path), output_path
        elif res_type == 'ics#':
            pixels = icon_1bit_to_pixels(data, 16)
            return save_icon_as_png(pixels, 16, output_path), output_path
        elif res_type == 'ics4':
            pixels = icon_4bit_to_pixels(data, 16)
            return save_icon_as_png(pixels, 16, output_path), output_path
        elif res_type == 'ics8':
            pixels = icon_8bit_to_pixels(data, 16)
            return save_icon_as_png(pixels, 16, output_path), output_path
        elif res_type == 'ICON':
            # 32x32 1-bit, no mask
            pixels = icon_1bit_to_pixels(data + b'\xff' * 128, 32)
            return save_icon_as_png(pixels, 32, output_path), output_path
        elif res_type == 'CURS':
            # 16x16 1-bit cursor with mask and hotspot
            pixels = icon_1bit_to_pixels(data, 16)
            return save_icon_as_png(pixels, 16, output_path), output_path
    except Exception as e:
        print(f"    Warning: icon extract failed for {res_type} {res_id}: {e}")

    return False, None


# ---------------------------------------------------------------------------
# PICT Extractor
# ---------------------------------------------------------------------------

def extract_pict(resource, output_dir, tool_name):
    """Extract a PICT resource. Save as raw PICT with 512-byte header for compat."""
    res_id = resource['id']
    data = resource['data']
    safe_name = tool_name.replace('/', '_').replace(' ', '_')

    # Save raw PICT (with standard 512-byte zero header prepended)
    pict_path = os.path.join(output_dir, f"{safe_name}_PICT_{res_id}.pict")
    with open(pict_path, 'wb') as f:
        f.write(b'\x00' * 512)  # Standard PICT header
        f.write(data)

    # Try to convert to PNG using sips (macOS built-in)
    png_path = os.path.join(output_dir, f"{safe_name}_PICT_{res_id}.png")
    try:
        result = subprocess.run(
            ['sips', '-s', 'format', 'png', pict_path, '--out', png_path],
            capture_output=True, timeout=10
        )
        if result.returncode == 0 and os.path.exists(png_path):
            os.remove(pict_path)  # Clean up raw PICT
            return True, png_path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return True, pict_path


# ---------------------------------------------------------------------------
# Sound Extractor
# ---------------------------------------------------------------------------

def extract_snd(resource, output_dir, tool_name):
    """Extract a 'snd ' resource to raw file, then convert with ffmpeg."""
    res_id = resource['id']
    res_name = resource['name'] or f"snd_{res_id}"
    data = resource['data']
    safe_name = tool_name.replace('/', '_').replace(' ', '_')
    safe_snd_name = res_name.replace('/', '_').replace(' ', '_')

    # Save raw snd resource
    raw_path = os.path.join(output_dir, f"{safe_name}_{safe_snd_name}_{res_id}.snd")
    with open(raw_path, 'wb') as f:
        f.write(data)

    # Try to parse and convert the snd resource
    wav_path = os.path.join(output_dir, f"{safe_name}_{safe_snd_name}_{res_id}.wav")
    if convert_snd_to_wav(data, wav_path):
        return True, wav_path

    return True, raw_path


def convert_snd_to_wav(snd_data, wav_path):
    """Convert a Mac 'snd ' resource to WAV.

    Format 1 'snd ' resource:
      offset 0: uint16 format (1 or 2)
      offset 2: uint16 num_data_formats (usually 1)
      offset 4: uint16 data_format_id (usually 5 = sampled)
      offset 6: uint32 init_option
      For format 1, sampled sound:
        After header: sound commands
        stdSndCmd (0x8051): offset to sound data header

      Sampled sound header:
        uint32 data_pointer (0 in resource)
        uint32 num_samples
        uint32 sample_rate (Fixed point 16.16)
        uint32 loop_start
        uint32 loop_end
        uint8  encoding (0=stdSH, 0xFF=extSH, 0xFE=cmpSH)
        uint8  base_freq
        [data follows for stdSH]
    """
    if len(snd_data) < 10:
        return False

    try:
        fmt = struct.unpack('>H', snd_data[0:2])[0]

        if fmt == 1:
            num_formats = struct.unpack('>H', snd_data[2:4])[0]
            offset = 4 + num_formats * 6  # skip data format entries

            # Read sound commands
            num_cmds = struct.unpack('>H', snd_data[offset:offset+2])[0]
            offset += 2

            sound_data_offset = None
            for _ in range(num_cmds):
                if offset + 8 > len(snd_data):
                    break
                cmd = struct.unpack('>H', snd_data[offset:offset+2])[0]
                param1 = struct.unpack('>H', snd_data[offset+2:offset+4])[0]
                param2 = struct.unpack('>I', snd_data[offset+4:offset+8])[0]

                if cmd in (0x8051, 0x0051):  # bufferCmd with dataPointerFlag
                    sound_data_offset = param2
                offset += 8

            if sound_data_offset is None:
                # Try the offset right after commands
                sound_data_offset = offset

        elif fmt == 2:
            # Format 2: reference count + num_cmds directly
            num_cmds = struct.unpack('>H', snd_data[4:6])[0]
            offset = 6
            sound_data_offset = None
            for _ in range(num_cmds):
                if offset + 8 > len(snd_data):
                    break
                cmd = struct.unpack('>H', snd_data[offset:offset+2])[0]
                param2 = struct.unpack('>I', snd_data[offset+4:offset+8])[0]
                if cmd in (0x8051, 0x0051):
                    sound_data_offset = param2
                offset += 8
            if sound_data_offset is None:
                sound_data_offset = offset
        else:
            return False

        if sound_data_offset >= len(snd_data):
            return False

        # Parse sampled sound header
        sh = snd_data[sound_data_offset:]
        if len(sh) < 22:
            return False

        _data_ptr = struct.unpack('>I', sh[0:4])[0]
        num_samples = struct.unpack('>I', sh[4:8])[0]
        sample_rate_fixed = struct.unpack('>I', sh[8:12])[0]
        encoding = sh[20]

        sample_rate = sample_rate_fixed >> 16  # Integer part of fixed-point
        if sample_rate == 0:
            sample_rate = 22050  # Default

        if encoding == 0x00:  # Standard sound header (stdSH)
            audio_data = sh[22:22+num_samples]
            bits_per_sample = 8
            num_channels = 1
        elif encoding == 0xFF:  # Extended sound header (extSH)
            # extSH layout:
            #   0-3:   data_ptr
            #   4-7:   num_channels (NOT num_samples)
            #   8-11:  sample_rate (fixed 16.16)
            #   12-15: loop_start
            #   16-19: loop_end
            #   20:    encoding (0xFF)
            #   21:    base_freq
            #   22-25: num_frames
            #   26-35: AIFF sample rate (80-bit extended)
            #   36-39: marker chunk
            #   40-43: instrument chunks ptr
            #   44-47: AES recording ptr
            #   48-49: sample size (bits per sample)
            #   50-63: future use / padding
            #   64+:   sample data
            if len(sh) < 64:
                return False
            num_channels = struct.unpack('>I', sh[4:8])[0]
            num_frames = struct.unpack('>I', sh[22:26])[0]
            bits_per_sample = struct.unpack('>H', sh[48:50])[0]
            if num_channels == 0:
                num_channels = 1
            if bits_per_sample == 0:
                bits_per_sample = 8
            byte_depth = max(1, bits_per_sample // 8)
            data_size = num_frames * num_channels * byte_depth
            audio_data = sh[64:64+data_size]
            num_samples = num_frames
        elif encoding == 0xFE:  # Compressed sound header (cmpSH)
            # MACE 3:1 or 6:1 compressed -- cannot easily decode without
            # the original Mac Sound Manager decompressor. Skip these.
            return False
        else:
            return False

        if len(audio_data) == 0:
            return False

        # Write WAV
        write_wav(wav_path, audio_data, sample_rate, bits_per_sample, num_channels)
        return True

    except Exception as e:
        return False


def write_wav(path, audio_data, sample_rate, bits_per_sample, num_channels):
    """Write a WAV file from raw PCM data."""
    byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
    block_align = num_channels * (bits_per_sample // 8)
    data_size = len(audio_data)

    with open(path, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))  # PCM
        f.write(struct.pack('<H', num_channels))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', byte_rate))
        f.write(struct.pack('<H', block_align))
        f.write(struct.pack('<H', bits_per_sample))
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))

        if bits_per_sample == 8:
            # Mac 8-bit audio is unsigned, WAV 8-bit is also unsigned - direct copy
            f.write(audio_data)
        else:
            # 16-bit: Mac is big-endian, WAV is little-endian
            for i in range(0, len(audio_data) - 1, 2):
                f.write(bytes([audio_data[i+1], audio_data[i]]))


# ---------------------------------------------------------------------------
# Text Extractors
# ---------------------------------------------------------------------------

def extract_text(resource):
    """Extract TEXT resource as string."""
    try:
        return resource['data'].decode('mac_roman', errors='replace')
    except:
        return None


def extract_str(resource):
    """Extract STR resource (pascal string)."""
    data = resource['data']
    if len(data) < 1:
        return None
    length = data[0]
    try:
        return data[1:1+length].decode('mac_roman', errors='replace')
    except:
        return None


def extract_str_list(resource):
    """Extract STR# resource (list of pascal strings)."""
    data = resource['data']
    if len(data) < 2:
        return []
    count = struct.unpack('>H', data[0:2])[0]
    strings = []
    offset = 2
    for _ in range(count):
        if offset >= len(data):
            break
        length = data[offset]
        offset += 1
        s = data[offset:offset+length].decode('mac_roman', errors='replace')
        strings.append(s)
        offset += length
    return strings


def extract_vers(resource):
    """Extract vers resource (version info)."""
    data = resource['data']
    if len(data) < 7:
        return None
    major = data[0]
    minor = (data[1] >> 4) & 0xF
    bugfix = data[1] & 0xF
    stage_map = {0x20: 'dev', 0x40: 'alpha', 0x60: 'beta', 0x80: 'release'}
    stage = stage_map.get(data[2], f'0x{data[2]:02x}')
    pre_release = data[3]

    # Short version string (pascal string at offset 6)
    if len(data) > 7:
        slen = data[6]
        short_ver = data[7:7+slen].decode('mac_roman', errors='replace')
    else:
        short_ver = f"{major}.{minor}.{bugfix}"

    # Long version string
    long_ver = None
    if len(data) > 7 + data[6]:
        loff = 7 + data[6]
        if loff < len(data):
            llen = data[loff]
            long_ver = data[loff+1:loff+1+llen].decode('mac_roman', errors='replace')

    return {
        'version': f"{major}.{minor}.{bugfix}",
        'stage': stage,
        'pre_release': pre_release,
        'short': short_ver,
        'long': long_ver
    }


# ---------------------------------------------------------------------------
# FDO88 Form Extractor
# ---------------------------------------------------------------------------

def extract_fdo88_form(resource, output_dir, tool_name):
    """Save raw FDO88 DB resource for later decompilation."""
    safe_name = tool_name.replace('/', '_').replace(' ', '_')
    db_type = resource['type']
    res_id = resource['id']

    filename = f"{safe_name}_{db_type}_{res_id}.fdo88"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, 'wb') as f:
        f.write(resource['data'])

    return output_path


# ---------------------------------------------------------------------------
# Master Extraction Pipeline
# ---------------------------------------------------------------------------

# Resource types we care about
ART_TYPES = {'PICT', 'ICN#', 'icl4', 'icl8', 'ics#', 'ics4', 'ics8', 'ICON', 'cicn', 'CURS', 'ppat'}
SOUND_TYPES = {'snd '}
TEXT_TYPES = {'TEXT', 'STR ', 'STR#'}
# Match ANY resource type starting with DB or db (case insensitive)
# Tools use non-standard IDs: db69, db81, db96, dbDD, dbAB, db45, db3F, db34, db32, DB1A, etc.
def _is_fdo_type(rtype):
    """Check if a resource type is an FDO88 form (DB/db prefix with any suffix)."""
    return (rtype.startswith('DB') or rtype.startswith('db')) and len(rtype) >= 4

FDO_TYPES = None  # We use _is_fdo_type() instead
META_TYPES = {'vers', 'Tinf', 'Tevt', 'AOtk'}
ICON_TYPES = {'ICN#', 'icl4', 'icl8', 'ics#', 'ics4', 'ics8', 'ICON', 'CURS'}


def process_tool(tool_dir, output_base, tool_name):
    """Process a single extracted tool directory."""
    result = {
        'name': tool_name,
        'files': [],
        'art': [],
        'sounds': [],
        'text': [],
        'fdo88_forms': [],
        'versions': [],
        'metadata': {},
        'resource_summary': {}
    }

    # Find all files in the tool directory
    for root, dirs, files in os.walk(tool_dir):
        for fname in files:
            if fname == '.DS_Store':
                continue

            filepath = os.path.join(root, fname)
            result['files'].append(filepath)

            # Read resource fork
            rsrc_data = read_resource_fork(filepath)
            if not rsrc_data or len(rsrc_data) < 16:
                # Check if the data fork itself is a resource fork (MacBinary)
                continue

            resources = parse_resource_fork(rsrc_data)
            if not resources:
                continue

            # Summarize resources
            type_counts = defaultdict(int)
            for res in resources:
                type_counts[res['type']] += 1
            result['resource_summary'] = dict(type_counts)

            # Create output directories
            art_dir = os.path.join(output_base, 'art', tool_name)
            sound_dir = os.path.join(output_base, 'sounds', tool_name)
            fdo_dir = os.path.join(output_base, 'fdo88', tool_name)

            for res in resources:
                rtype = res['type']

                # Art extraction
                if rtype in ICON_TYPES:
                    os.makedirs(art_dir, exist_ok=True)
                    success, path = extract_icon(res, art_dir, tool_name)
                    if success and path:
                        result['art'].append({
                            'type': rtype,
                            'id': res['id'],
                            'name': res['name'],
                            'path': os.path.relpath(path, output_base),
                            'size': res['size']
                        })

                elif rtype == 'PICT':
                    os.makedirs(art_dir, exist_ok=True)
                    success, path = extract_pict(res, art_dir, tool_name)
                    if success and path:
                        result['art'].append({
                            'type': 'PICT',
                            'id': res['id'],
                            'name': res['name'],
                            'path': os.path.relpath(path, output_base),
                            'size': res['size']
                        })

                # Sound extraction
                elif rtype == 'snd ':
                    os.makedirs(sound_dir, exist_ok=True)
                    success, path = extract_snd(res, sound_dir, tool_name)
                    if success and path:
                        result['sounds'].append({
                            'id': res['id'],
                            'name': res['name'],
                            'path': os.path.relpath(path, output_base),
                            'size': res['size']
                        })

                # Text extraction
                elif rtype == 'TEXT':
                    text = extract_text(res)
                    if text:
                        result['text'].append({
                            'type': 'TEXT',
                            'id': res['id'],
                            'name': res['name'],
                            'content': text
                        })

                elif rtype == 'STR ':
                    text = extract_str(res)
                    if text:
                        result['text'].append({
                            'type': 'STR',
                            'id': res['id'],
                            'name': res['name'],
                            'content': text
                        })

                elif rtype == 'STR#':
                    strings = extract_str_list(res)
                    if strings:
                        result['text'].append({
                            'type': 'STR#',
                            'id': res['id'],
                            'name': res['name'],
                            'content': '\n'.join(strings)
                        })

                # Version info
                elif rtype == 'vers':
                    ver = extract_vers(res)
                    if ver:
                        result['versions'].append(ver)

                # FDO88 forms
                elif _is_fdo_type(rtype):
                    os.makedirs(fdo_dir, exist_ok=True)
                    path = extract_fdo88_form(res, fdo_dir, tool_name)
                    result['fdo88_forms'].append({
                        'type': rtype,
                        'id': res['id'],
                        'name': res['name'],
                        'path': os.path.relpath(path, output_base),
                        'size': res['size']
                    })

                # AOtk (tool code) - just note metadata
                elif rtype == 'AOtk':
                    result['metadata']['has_aotk'] = True
                    result['metadata']['aotk_size'] = res['size']

    return result


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <extracted_tools_dir> <output_dir>")
        sys.exit(1)

    tools_dir = sys.argv[1]
    output_dir = sys.argv[2]

    os.makedirs(output_dir, exist_ok=True)

    all_results = {}
    total_art = 0
    total_sounds = 0
    total_text = 0
    total_fdo = 0

    # Process each tool directory
    tool_dirs = sorted([d for d in os.listdir(tools_dir)
                       if os.path.isdir(os.path.join(tools_dir, d)) and d != '.DS_Store'])

    print(f"Processing {len(tool_dirs)} tools...\n")

    for tool_name in tool_dirs:
        tool_path = os.path.join(tools_dir, tool_name)
        print(f"  [{tool_name}]", end='', flush=True)

        result = process_tool(tool_path, output_dir, tool_name)
        all_results[tool_name] = result

        n_art = len(result['art'])
        n_snd = len(result['sounds'])
        n_txt = len(result['text'])
        n_fdo = len(result['fdo88_forms'])

        total_art += n_art
        total_sounds += n_snd
        total_text += n_txt
        total_fdo += n_fdo

        parts = []
        if n_art: parts.append(f"{n_art} art")
        if n_snd: parts.append(f"{n_snd} snd")
        if n_txt: parts.append(f"{n_txt} txt")
        if n_fdo: parts.append(f"{n_fdo} fdo")

        if parts:
            print(f" -> {', '.join(parts)}")
        else:
            print(f" -> (no extractable resources)")

    # Write master manifest
    manifest = {
        'extraction_date': __import__('datetime').datetime.now().isoformat(),
        'total_tools': len(tool_dirs),
        'total_art': total_art,
        'total_sounds': total_sounds,
        'total_text': total_text,
        'total_fdo88_forms': total_fdo,
        'tools': {}
    }

    for name, result in all_results.items():
        # Don't include raw data in JSON manifest
        tool_entry = {
            'name': result['name'],
            'art_count': len(result['art']),
            'sound_count': len(result['sounds']),
            'text_count': len(result['text']),
            'fdo88_count': len(result['fdo88_forms']),
            'versions': result['versions'],
            'resource_summary': result['resource_summary'],
            'has_aotk': result['metadata'].get('has_aotk', False),
            'art': result['art'],
            'sounds': result['sounds'],
            'text': [{'type': t['type'], 'id': t['id'], 'name': t['name'],
                      'content': t['content'][:2000]} for t in result['text']],
            'fdo88_forms': result['fdo88_forms']
        }
        manifest['tools'][name] = tool_entry

    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Extraction complete!")
    print(f"  Tools processed: {len(tool_dirs)}")
    print(f"  Art extracted:   {total_art}")
    print(f"  Sounds extracted: {total_sounds}")
    print(f"  Text resources:  {total_text}")
    print(f"  FDO88 forms:     {total_fdo}")
    print(f"  Manifest:        {manifest_path}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
