# FDO88 Opcode Conflicts: Low-Bit vs High-Bit Dispatch

## The Mirroring Assumption is Wrong

The FDO88 engineering manual and atomforge both assume that low-bit opcodes
(0x00-0x7F) are "mirrors" of high-bit opcodes (0x80-0xFF) -- same command,
different parameter encoding (fixed-size vs byte-count prefix). This is
documented in CLAUDE.md:

> FDO88 low-bit opcodes ($00-$7F) are mirrors of high-bit opcodes ($80-$FF)
> with fixed-size params instead of byte-count prefix

**This is only partially true.** The AOL 2.7 binary has completely independent
dispatch tables for low-bit and high-bit opcodes in FormsCreation (CODE 21):

- **High-bit (0x80+)**: Handled at CODE 21:0x2818 with subtraction-based dispatch
- **Low-bit (0x00-0x7F)**: Handled at CODE 21:0x2BD8 with a 91-entry jump table

While many low-bit opcodes DO perform similar functions to their high-bit
counterparts (especially the flag set/clear pairs), **at least 6 low-bit
opcodes do completely different things** from their assumed high-bit mirrors.

## Confirmed Conflicts

| Low-Bit | Atomforge Assumes | Actual Function | Param Mismatch |
|---------|------------------|-----------------|----------------|
| 0x21 | fdo$Field16 (10 bytes) | ClearDialogMode (0 bytes) | CRITICAL: 10 bytes overconsume |
| 0x23 | fdo$Title (string) | SetConnectionState (1 byte) | CRITICAL: string vs byte |
| 0x26 | fdo$Window16 (9 bytes) | RefreshForm (0 bytes) | CRITICAL: 9 bytes overconsume |
| 0x28 | fdo$TextDesc (4 bytes) | LoadFormFromDB (0 bytes) | CRITICAL: 4 bytes overconsume |
| 0x2A | fdo$Domain (string) | BuildCompleteForm (0 bytes) | CRITICAL: string overconsume |
| 0x2C | fdo$MakeWindowCurrent (4 bytes) | SetNoCloseFlag (0 bytes) | CRITICAL: 4 bytes overconsume |

**Impact on atomforge decoder:** When the decoder encounters these opcodes in
a live FDO88 stream, it reads the wrong number of parameter bytes, which
misaligns the stream pointer. All subsequent opcodes in the stream are
decoded incorrectly. This is a corruption bug that cascades through the
entire form.

## Why This Wasn't Caught Earlier

1. **Canned forms rarely use these opcodes.** The conflicting opcodes are
   mostly server-only commands (SetConnectionState, LoadFormFromDB, etc.)
   that appear in live protocol streams from the host, not in DB resources.
   Atomforge was validated against 2,485 extracted DB forms -- none contain
   these opcodes.

2. **The manual describes the cross-platform spec.** The low-bit commands
   that conflict are Mac-specific server infrastructure added by AOL's
   engineering team. They weren't in the original cross-platform FDO88
   specification that the manual documents.

3. **No live 2.7 captures existed until today.** Without a working AOL 2.7
   connection to capture server-originated FDO88 streams, these opcodes
   were never encountered.

## Complete Low-Bit Opcode Map

See `binary_analysis/lowbit_opcode_map.md` for the full 73-handler dispatch
table with all identified functions, parameters, and conflict flags.

Key statistics:
- 91 dispatch entries (opcodes 0x01-0x5B)
- 73 implemented, 18 NOP
- 6 confirmed conflicts with atomforge
- 14 server-only commands (never in canned forms)
- 30 flag set/clear commands (15 pairs, zero params)
- 1 deprecated command (0x52: "Outdated switch 82 found!")

## Fixes Needed in Atomforge

### Immediate (blocking the connection)
1. Register opcode 0x23 as `fdo$SetOnline` with 1-byte param (not string)
2. Fix `LOW_BIT_PARAM_SIZES[0x23]` from `-3` (string) to `1` (single byte)
3. Fix `Fdo88Formatter` case `0x23` to not call `formatTitle`

### Short-term (decoder correctness)
4. Fix `LOW_BIT_PARAM_SIZES[0x21]` from `10` to `0`
5. Fix `LOW_BIT_PARAM_SIZES[0x26]` from `9` to `0`
6. Fix `LOW_BIT_PARAM_SIZES[0x28]` from `4` to `0`
7. Fix `LOW_BIT_PARAM_SIZES[0x2A]` from `-3` (string) to `0`
8. Fix `LOW_BIT_PARAM_SIZES[0x2C]` from `4` to `0`

### Medium-term (complete protocol support)
9. Register all 73 low-bit opcodes with correct names and param sizes
10. Add DSL methods for server-only commands (SetConnectionState, Signoff, etc.)
11. Update the Fdo88Formatter to decompile low-bit opcodes with their real names

## Update to CLAUDE.md

The statement about low-bit mirroring should be corrected:

> FDO88 low-bit opcodes ($00-$7F) share the dispatch table with high-bit
> opcodes ($80-$FF) but have INDEPENDENT handlers in FormsCreation.
> Many perform similar functions to their high-bit counterparts, but at
> least 6 opcodes (0x21, 0x23, 0x26, 0x28, 0x2A, 0x2C) do completely
> different things. See documentation/fdo88_opcode_conflicts.md.
