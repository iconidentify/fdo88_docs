# FDO88 Manual

A searchable, browseable reference for **FDO88** (Form Definition Opcode 88) -- the proprietary remote GUI protocol that powered America Online's client-server interface from 1988 through the mid-1990s.

**[View the manual online](https://iconidentify.github.io/fdo88_docs/)**

## What is FDO88?

FDO88 is a bytecode-compiled programming language developed internally at Quantum Computer Services (later America Online) in 1988. It controlled the appearance and functionality of every window, button, icon, list, menu, and form that AOL members saw on screen.

When a user interacted with the AOL client software, the client sent a token to AOL's host servers (running on Stratus fault-tolerant computers). The server responded with an FDO data stream -- a sequence of opcodes and parameters instructing the client how to construct and display the UI. This is conceptually similar to what HTML/CSS does for the web, but FDO is a binary compiled opcode stream transmitted over dial-up, predating HTML by three years.

### Platforms

FDO88 targeted three platforms, reflecting AOL's 1988 multi-platform expansion:

- **Macintosh** (Motorola 68000, big-endian)
- **Apple II** (MOS 6502, little-endian)
- **Tandy 1000** (IBM-compatible DOS)

The dual endianness of these platforms is why FDO88 uses "flipped integers" -- 2-byte values transmitted low byte first to accommodate the 6502.

### AOL Mac versions powered by FDO88

FDO88 was the rendering engine behind the classic AOL for Macintosh releases:

- **AOL 2.0** (1994)
- **AOL 2.5** (1995)
- **AOL 2.6** (1996)
- **AOL 2.7** (1997)

These were the last Mac versions built on FDO88. Starting with AOL 3.0 for Mac, the client transitioned to FDO91.

### FDO88 vs FDO91

FDO91 succeeded FDO88 in 1991. All AOL for Windows versions (1.0 through 5.0+) ran on FDO91 exclusively -- Windows never used FDO88. On the Mac side, FDO88 powered versions 2.0 through 2.7, after which FDO91 took over with version 3.0.

| | FDO88 | FDO91 |
|---|---|---|
| Year | 1988 | 1991 |
| Platforms | Macintosh, Apple II, Tandy | Windows, Mac v3.0+ |
| Mac versions | 2.0, 2.5, 2.6, 2.7 | 3.0+ |
| Windows versions | None | All |
| Tooling | `form_edit`, Stratus database | VPD, AMP |

## About this document

The source material is the **FDO88 Manual, Release 1.0** (January 1994), an internal America Online document marked "America Online Confidential." The manual was OCR-processed from a scanned physical copy into structured JSON, then rendered into the interactive viewer hosted here.

### Contents

- **119 commands** covering window management, field definitions, content display, navigation, sound, menus, and list boxes
- **38 glossary terms**
- **43 reference tables** (window types, field types, field booleans, switch values, etc.)
- **6 code samples** with annotated FDO streams
- **2 chapters**: Introduction and FDO88 Description
- **6 appendices**: Command Reference (A), Sample FDO Streams (B), Reference Tables (C), Quick Reference Lists (D), Menu Operation Codes (E), Macintosh Window Types (F)

### Command structure

Each FDO command has an alphabetic name (e.g., `fdo$Window16`, `fdo$dispch`, `fdo$Text`), a numeric opcode, and zero or more arguments. Commands fall into two classes:

- **Base commands** (opcodes 0-127): no byte-count argument
- **Byte-count commands** (opcodes 128-255): include an explicit length prefix for variable-length parameters
- **Extended commands**: use opcode 248 (`$F8`) plus a sub-opcode to expand the command space beyond the original 128 slots

### Dispatch system

User interactions trigger **MOP codes** (Menu Operation Codes) -- 6-byte dispatch structures embedded in field definitions. Key MOPs include `Ask_DB` (fetch a form), `Send_Form` (submit field data to host), `Mop_Local_Token` (execute locally), and `Ask_Indirect` (parameterized fetch from a list selection).

## Running locally

Open `index.html` directly in a browser. No server required -- the JSON data is inlined via a script tag.

## Related resources

- [Matt Mazur: Remembering AOL's FDO91 Programming Language](https://mattmazur.com/2012/01/28/remembering-aols-fdo91-programming-language/)
- [The AOL Protocol (theaolprotocol.txt)](https://justinakapaste.com/the-aol-protocol/)
- [notaol: AOL P3/FDO client implementation](https://github.com/chfoo/notaol)
- [AOL FDO Traces (Internet Archive)](https://archive.org/details/aol-fdo-traces)
- [AOL Protocol Documentation (Internet Archive)](https://archive.org/details/aol_20210605)

## License

[MIT](LICENSE)
