# AOL 2.7 Connection Sequence

## Current Understanding (Updated 2026-04-06)

### What Works
- P3 handshake: INIT/ACK/SD
- Credential exchange: Dd
- AT token: client processes FDO88 data (sounds play, opcodes execute)
- fdo$break chunking at opcode boundaries
- FDO88 form content (DB16_252 welcome screen verified correct)
- Sequence numbering (after SD handshake fix)

### What Doesn't Work Yet
- Client stays at "Opening connection" -- sign-on progress screen not dismissed
- Forms render as Network News entries (OT/oT) or process without creating
  a visible window (AT)

### Known Token Functions (Verified)
| Token | Hex | Function | Verified From |
|-------|-----|----------|---------------|
| EW | 0x4557 | SetConnectionState(1) | CODE 9:0x07F6 |
| EC | 0x4543 | SetConnectionState(0) | CODE 9:0x0802 |
| OT | 0x4F54 | Network News alert | 3.0 source ASYNC/async.c:191, confirmed by screenshot |
| oT | 0x6F54 | Network News text entries | Confirmed by screenshot |
| XS | 0x5853 | Sign-OFF / ForceOff | 3.0 source ASYNC/async.c:203 |
| SD | 0x5344 | Sign-on data (pre-stored) | CODE 9:0x0858 |
| D* | 0x442A | Disconnect | 3.0 TOKEN_DSTAR confirmed |
| AT | 0x4154 | Form/atom stream delivery | 3.0 atomizer.c, client processes it |
| At | 0x4174 | Form/atom stream (3-byte SID) | 3.0 atomizer.c |
| at | 0x6174 | Form/atom stream (4-byte SID) | 3.0 atomizer.c |
| aT | 0x6154 | Form/atom stream (0-byte SID) | 3.0 atomizer.c |

### Key FDO88 Switch Values (From Official Manual)
| Switch | Name | Function |
|--------|------|----------|
| 87 | CloseSignOn | "Closes sign on progress screens, broadcasts 'We are now online' to tools" |
| 48 | ShowPasswords | Enables password fields on sign-on form |
| 200 | SetMailboxICON | "Sets flag indicating Welcome screen is completed" |
| 32 | switch_32 | Used in welcome screen form |

### Current Investigation: Missing P3 SS/SSR Handshake

The P3 protocol spec defines the handshake as:
```
INIT ($23) -> SS ($21) -> SSR ($22) -> ACK ($24) -> DATA ($20)
```

Dialtone currently sends:
```
INIT -> ACK -> SD DATA
```

The SS (Server Setup, type 0x21) and SSR (Setup Response, type 0x22) frames
are missing. The client's state machine may require the full SS/SSR exchange
to advance past "Opening connection." This is the current leading theory.

### FDO88 Form Delivery
Forms are sent via AT token (0x4154) with a 2-byte stream ID prefix.
FDO88 data is split at fdo$break boundaries, each chunk in a separate
AT frame with the same stream ID. Last chunk ends with fdo$enddef (0x09).

The fdo$Switch CloseSignOn (87) should be included in the form stream
to signal "we are now online" -- but it only works if the form goes
through FormsCreation, which may require the P3 handshake to complete first.

## Verified Binary Analysis (Still Correct)
- INIT packet layout: see init_packet_disassembly.md
- P3 sequence numbering: SD handshake consumes TX=16, first DATA uses TX=17
- Low-bit opcode conflicts: see fdo88_opcode_conflicts.md
- FDO88 opcode 0x23 = SetConnectionState (CODE 21:0x2EA6)
- Online Database forms extracted: binary_analysis/online_database_forms/
