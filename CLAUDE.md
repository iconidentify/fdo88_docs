# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dialtone Tech Notes -- a static HTML/JS documentation site for AOL 2.7 reverse engineering. Covers the FDO88 binary GUI protocol, P3 transport layer, and the 1990s underground Mac AOL tool scene. Hosted at `iconidentify.github.io/fdo88_docs/`. Branded as Dialtone (orange #fc9d2c on dark navy #04060c).

## No Emojis

Do not use emojis in any output: no commits, no UI, no code, no READMEs.

## Architecture

The site is a single `index.html` (no frameworks, no build step) that loads three inline JS data files:

- `aol_manual_output.js` -- `window.__MANUAL_DATA`, 119 FDO88 commands from the OCR'd AOL engineering manual
- `tool_manifest.js` -- `window.__TOOL_MANIFEST`, base64-encoded art (PNGs), sounds (WAVs), and text from 83 extracted Mac AOL tools (~10MB)
- `fdo88_forms.js` -- `window.__FDO88_FORMS`, 2,485 decompiled FDO88 form sources grouped by tool (~5.5MB)

The site runs from `file://` with no server required. Deep linking works via `#tool/ToolName` hash routes.

## Related Projects (same machine)

- **atomforge-fdo-java** (`/Users/chrisk/Documents/source/atomforge-fdo-java`) -- Java 21 FDO88/FDO91 compiler and decompiler. This repo's decompiled forms come from its `Fdo88Decompiler` class. Changes to formatters there require regenerating `fdo88_forms.js`.
- **Dialtone** (`/Users/chrisk/Documents/source/Dialtone`) -- AOL server reimplementation (Java, Netty). Uses atomforge-fdo for FDO88 compilation.

## Reverse Engineering Pipeline

The full pipeline is scripted in `scripts/reverse_engineer.sh`. Individual steps:

### 1. Extract StuffIt archives
```
# .sit files in "binary sources/tools/" -> extracted to extracted_tools/
unar -o extracted_tools/ToolName -f "binary sources/tools/ToolName.sit"
```

### 2. Extract resources (art, sounds, text, FDO88 binaries)
```
python3 scripts/extract_resources.py extracted_tools site_data
```
Requires macOS (resource fork access via `..namedfork/rsrc`), Python 3 with Pillow. Outputs PNGs, WAVs, text, and raw `.fdo88` binary files into `site_data/`.

### 3. Decompile FDO88 forms
```
cd scripts
javac -cp /path/to/atomforge-fdo-2.0.0-SNAPSHOT.jar Fdo88BatchDecompile.java
java -cp /path/to/atomforge-fdo-2.0.0-SNAPSHOT.jar:. Fdo88BatchDecompile ../site_data/fdo88 ../site_data/fdo88_decompiled
```
Requires Java 21+ and the built atomforge JAR. Produces `fdo88_manifest.json` with all decompiled source.

### 4. Rebuild JS data files
After extraction or decompilation changes, rebuild the inline JS files. The `fdo$` prefix must be stripped from decompiled source -- FDO88 commands are displayed without the prefix (it's implied). The rebuild script in `reverse_engineer.sh` handles this.

### 5. Rebuild atomforge JAR (when modifying formatters/decoders)
```
cd /Users/chrisk/Documents/source/atomforge-fdo-java
mvn package -DskipTests
# Then re-run steps 3-4
```
Run `mvn test` to verify -- expects 140/140 golden round-trips and ~98% community accuracy.

## Key Technical Facts (verified from binary analysis)

- AOL 2.7 Mac client: 57 CODE segments, 448 resources, 44 types, 851KB resource fork
- AOL4Free patches AOL **2.6** (not 2.7) using **ResCompare** by Michael Hecht (v4.0.3), not a custom framework
- DB resource types for FDO88 forms use non-standard IDs across tools (db69, db81, db96, dbAB, dbDD, etc.), not just DB00-DB19
- FDO88 low-bit opcodes ($00-$7F) are mirrors of high-bit opcodes ($80-$FF) with fixed-size params instead of byte-count prefix
- Mac `snd` resources with encoding byte $FE (cmpSH/MACE compressed) cannot be decoded to WAV; $FF (extSH) can
- The Gemini API key for image generation is stored on i9beef at `/etc/opencode/cloud-api-keys.env`

## Content Accuracy Rules

- Every claim about AOL4Free, protocol details, or binary structure must trace to actual binary analysis or the verified documentation in `documentation/`. Do not fabricate technical details.
- Do not invent names of people, legal citations, or specific mechanisms not present in the source material.
- The AOL4Free author's handle "Happy Hardcore" comes from the binary's own vers/TEXT resources. No real name is known.
