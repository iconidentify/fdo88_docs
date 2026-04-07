# Dialtone AOL 2.7 Mac Client Support - Protocol Reference

Extracted from disassembly of the AOL 2.7 client binary (851KB, 57 CODE segments),
171 canned FDO88 forms, 42 string tables, and cross-referenced with Dialtone's
existing AOL 3.0 implementation and the official FDO88 Manual.

## Client Identification

```
Version:   2.7 (vers resource: v2.112)
Copyright: 1987-1996 America Online, Inc.
Platform:  Macintosh (68k)
Serial ID: "A-OL" (STR# 10011)
TCP ID:    "TCPa" (STR# 1300)
```

## Token Map (Verified)

### Tokens the Server Should Send
| Token | Hex | Purpose | Payload |
|-------|-----|---------|---------|
| AT | 0x4154 | FDO88 form delivery | 2-byte stream ID + FDO88 data |
| EW | 0x4557 | Set online state | Empty (no stream ID) |

### Tokens the Server Should NOT Send
| Token | Hex | Why Not |
|-------|-----|---------|
| OT | 0x4F54 | Network News, not forms (3.0 source confirms) |
| oT | 0x6F54 | Network News text entries (screenshot confirms) |
| XS | 0x5853 | Sign-OFF / disconnect |
| D* | 0x442A | Disconnect |
| aT | 0x6154 | Needs investigation -- may be needed for auth transition |

### Tokens the Client Sends
| Token | Hex | Purpose |
|-------|-----|---------|
| Dd | 0x4464 | Credentials (screen name + password) |

## P3 Protocol

### Current Handshake (Incomplete)
```
C->S:  INIT (0xA3)  TX=127, RX=127
S->C:  ACK  (0x24)  TX=127, RX=127
S->C:  SD   (0x20)  TX=16,  token=SD
C->S:  Dd   (0xA0)  TX=16,  credentials
```

### Spec Handshake (May Be Required)
```
C->S:  INIT (0xA3)
S->C:  SS   (0x21)  <-- MISSING from Dialtone
C->S:  SSR  (0x22)  <-- MISSING from Dialtone
S->C:  ACK  (0x24)
S->C:  DATA (0x20)  tokens start flowing
```

The missing SS/SSR exchange is the current leading theory for why the
client stays at "Opening connection."

### P3 Constants
| Constant | Value | Purpose |
|----------|-------|---------|
| P3 state block | A5-0x5356 | Global connection state |
| Buffer size | 0x0270 (624) | P3 buffer allocation |
| Max payload | 0x0080 (128) | Max payload per DATA packet |
| Sync byte | 0x5A ('Z') | Frame sync |

### Sequence Numbering
- SD handshake frame consumes TX=16
- Server must advance TX counter after SD (setLastSentDataTx(0x10))
- First AT/EW frame uses TX=17

## FDO88 Form Delivery

### Using AT Token
```
AT frame: [5A][CRC:2][LEN:2][TX][RX][0x20][41][54][SID:2][FDO88 data][0D]
```

Split at fdo$break (0x16) boundaries. Same stream ID across chunks.

### Key FDO88 Switch Commands (From Official Manual)

| Switch | Name | Function |
|--------|------|----------|
| 87 | CloseSignOn | Closes sign-on screens, broadcasts "online" to tools |
| 48 | ShowPasswords | Enables password fields on sign-on form |
| 200 | SetMailboxICON | Marks welcome screen complete |

### FDO88 Opcode 0x23 (SetConnectionState)
Low-bit opcode 0x23 calls SetConnectionState (CODE 21:0x2EA6 -> CODE 9:0x009A).
This is NOT the same as fdo$Title (high-bit 0xA3). See fdo88_opcode_conflicts.md.

## Low-Bit Opcode Conflicts

Six low-bit opcodes do completely different things from their high-bit
counterparts. See fdo88_opcode_conflicts.md for details:

| Low-Bit | High-Bit Name | Actual Function |
|---------|--------------|-----------------|
| 0x21 | fdo$Field16 | ClearDialogMode |
| 0x23 | fdo$Title | SetConnectionState |
| 0x26 | fdo$Window16 | RefreshForm |
| 0x28 | fdo$TextDesc | LoadFormFromDB |
| 0x2A | fdo$Domain | BuildCompleteForm |
| 0x2C | fdo$MakeWindowCurrent | SetNoCloseFlag |

## Online Database

The client's canned forms are in the Online Database file:
`Online Files/Online Database` (74,604 byte resource fork, 269 resources, 140 FDO88 forms)

Key forms:
| Resource | ID | Description |
|----------|-----|-------------|
| DB14 | 161 | Sign-On Screen (667 bytes) |
| DB14 | 163 | Sign-On Screen variant (497 bytes) |
| DB16 | 251 | Main Menu (577 bytes) |
| DB16 | 252 | Welcome Screen (254 bytes) |

Extracted to: `binary_analysis/online_database_forms/`

## Binary Analysis Infrastructure

Pre-extracted resources at `binary_analysis/`:
- `code_segments/CODE_XX.bin` -- all 57 CODE segments
- `jump_table.json` -- 1,614 jump table entries
- `disassemble.py` -- 68k disassembler with JT resolution
- `lowbit_opcode_map.md` -- complete 73-handler FormsCreation dispatch
- `online_database_forms/` -- 140 FDO88 forms from Online Database
- `official_tools_fdo88/` -- 21 forms from official AOL tools
