# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dialtone Tech Notes -- a static HTML/JS documentation site for AOL 2.7 reverse engineering. Covers the FDO88 binary GUI protocol, P3 transport layer, and the 1990s underground Mac AOL tool scene. Hosted at `iconidentify.github.io/fdo88_docs/`. Branded as Dialtone (orange #fc9d2c on dark navy #04060c).

## No Emojis

Do not use emojis in any output: no commits, no UI, no code, no READMEs.

## Architecture

The site is a single `index.html` (no frameworks, no build step) that loads inline JS data files:

- `aol_manual_output.js` -- `window.__MANUAL_DATA`, 119 FDO88 commands from the OCR'd AOL engineering manual
- `tool_manifest.js` -- `window.__TOOL_MANIFEST`, base64-encoded art (PNGs), sounds (WAVs), and text from 83 extracted Mac AOL tools (~10MB)
- `fdo88_forms.js` -- `window.__FDO88_FORMS`, 2,485 decompiled FDO88 form sources grouped by tool (~5.5MB)
- `aol4free_docs.js` -- `window.__AOL4FREE_DOCS`, AOL4Free documentation chapters
- `disasm_data/disasm_index.js` -- `window.__DISASM_INDEX`, segment manifest for the disassembly viewer
- `disasm_data/code_NN.js` -- `window.__DISASM_CODE_NN`, per-segment disassembly data (loaded on demand)

The site runs from `file://` with no server required. Deep linking works via `#tool/ToolName` and `#disasm/CODE_N/0xOFFSET` hash routes.

## Disassembly Viewer

The `#disasm` section is an interactive 68k disassembly workbench with:
- Architecture-agnostic common instruction schema (68k first, x86-32 next)
- Virtual scrolling for segments with 14,000+ instructions
- 9 instruction type colors (call/branch/jump/return/trap/data/stack/arith/nop)
- Clickable cross-segment xref navigation
- Function headers with stack frame inference
- Trap name hover tooltips
- Compact mode and bytes toggle

The `disasm_data/` directory contains pre-generated JS files (one per CODE segment). To regenerate, use the tools in the chonkback repo (`binary_analysis/generate_disasm_data.py`).

## Related Projects (same machine)

- **chonkback** (`/Users/chrisk/Documents/source/chonkback`) -- Reverse engineering workbench. Contains binary_analysis/ (disassembler, auto_re harness, code segments), chonkback_research_os (MCP server), extraction scripts, and all binary source materials. Regenerating `disasm_data/` requires running tools from this repo.
- **atomforge-fdo-java** (`/Users/chrisk/Documents/source/atomforge-fdo-java`) -- Java 21 FDO88/FDO91 compiler and decompiler. This repo's decompiled forms come from its `Fdo88Decompiler` class.
- **Dialtone** (`/Users/chrisk/Documents/source/Dialtone`) -- AOL server reimplementation (Java, Netty). Uses atomforge-fdo for FDO88 compilation.

## Key Technical Facts (verified from binary analysis)

- AOL 2.7 Mac client: 57 CODE segments, 448 resources, 44 types, 851KB resource fork
- AOL4Free patches AOL **2.6** (not 2.7) using **ResCompare** by Michael Hecht (v4.0.3), not a custom framework
- DB resource types for FDO88 forms use non-standard IDs across tools (db69, db81, db96, dbAB, dbDD, etc.), not just DB00-DB19
- FDO88 low-bit opcodes ($00-$7F) and high-bit opcodes ($80-$FF) share the FormsCreation dispatch but have INDEPENDENT handlers. Many perform similar functions, but at least 6 opcodes (0x21, 0x23, 0x26, 0x28, 0x2A, 0x2C) do completely different things.
- Mac `snd` resources with encoding byte $FE (cmpSH/MACE compressed) cannot be decoded to WAV; $FF (extSH) can

## Protocol Documentation

Reverse-engineered protocol specs in `documentation/`:

- `aol27_connection_sequence.md` -- connection flow and current investigation status
- `init_packet_disassembly.md` -- annotated 68k disassembly of the INIT packet builder with field map
- `fdo88_form_delivery.md` -- form delivery protocol (AT token + fdo$break chunking)
- `fdo88_opcode_conflicts.md` -- 6 low-bit opcodes that differ from their high-bit counterparts
- `at_token_framing.md` -- At/AT/at/aT token wire format and stream ID encoding
- `dialtone_aol27_support.md` -- Dialtone server integration reference

Key protocol facts verified from binary:
- Form delivery uses P3 DATA frames with token "AT" (0x4154) with 2-byte stream ID
- Multi-frame forms split at fdo$break boundaries, one AT frame per chunk
- Auth transition triggered by undocumented FDO88 opcode 0x23 (SetConnectionState), NOT by `aT` token
- The `aT` token (0x6154) is AOL 3.0+ only -- 2.7 has no handler for it
- INIT token bytes come from the vNum resource, not Gestalt
- OT (0x4F54) is Network News, NOT form delivery (confirmed by 3.0 source + screenshots)
- XS (0x5853) is sign-OFF, NOT sign-on (confirmed by 3.0 source)
- fdo$Switch CloseSignOn (87) = "broadcasts 'We are now online' to tools" (from FDO88 Manual)
- P3 handshake may require SS (0x21) / SSR (0x22) exchange before DATA flow

## Content Accuracy Rules

- Every claim about AOL4Free, protocol details, or binary structure must trace to actual binary analysis or the verified documentation in `documentation/`. Do not fabricate technical details.
- Do not invent names of people, legal citations, or specific mechanisms not present in the source material.
- The AOL4Free author's handle "Happy Hardcore" comes from the binary's own vers/TEXT resources. No real name is known.
