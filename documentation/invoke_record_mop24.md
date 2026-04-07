# invoke_record (MOP $24) -- Binary Analysis

Disassembled from AOL 2.7 Mac client. The invoke_record dispatch is the
most misunderstood MOP in the FDO88 protocol. Despite its name, it does
NOT directly invoke database records by DB type and ID.

## Dispatch Record Wire Format

The `fdo$dispch` opcode stores a 6-byte dispatch record on each form
element at structure offset `$A8`:

```
byte 0: MOP code      ($24 = invoke_record)
byte 1: token_hi      (usually $00)
byte 2: token_lo      (usually $00)
byte 3: info1         (action code)
byte 4: info2         (parameter high byte)
byte 5: info3         (parameter low byte)
```

Source: atomforge-fdo-java `Dispatch.java`, confirmed by CODE 27:0x04A0
which copies 3 words (6 bytes) from element+$A8.

## Info Byte Encoding

The 3 info bytes do NOT encode a DB resource type and record ID.
They encode an **action code** and optional parameters:

- **info1** (byte 3): Action code / event ID
- **info2** (byte 4): Parameter high byte
- **info3** (byte 5): Parameter low byte
- Parameters combined as `(info2 << 8) | info3` in some handlers

### Bit 7 of info1 Controls Dispatch Mode

- **Bit 7 clear** (info1 < $80): Local dispatch through a 145-entry
  jump table in CODE 4 (Events) at 0x23D0. Uses `info1 - 1` as index.
- **Bit 7 set** (info1 >= $80): Remote dispatch. Builds a P3 protocol
  message with the 3 info bytes and sends it to the server. The server
  decides what action to take.

## Execution Path (Traced from Binary)

### Button Click Flow

1. CODE 27 (MOPs):0x04C4 -- Button click handler
   - Reads dispatch record from element+$A8 (6 bytes)
   - Calls 0x0450 to extract dispatch info based on element type

2. CODE 27:0x02FE -- Dispatch processor
   - Sends form ID to server via P3:0x568E
   - Copies 6-byte dispatch record to global at A5-$4170
   - Posts event via Events:0x0F8C

3. CODE 27:0x206C -- Event handler (called from event loop)
   - Re-extracts dispatch info from form element
   - Calls CODE 14 (Dbase):0x01DE to parse dispatch record
   - Dispatches through MOP jump table at 0x2250

4. CODE 27:0x2636 -- MOP $24 handler
   - Reads 3 info bytes from globals (A5-$2ED1, A5-$2ED0, A5-$2ECF)
   - Pushes as 3 word parameters
   - Calls CODE 4 (Events):0x22D8

5. CODE 4:0x22DC -- invoke_record event handler
   - Computes `d4 = (info2 << 8) | info3` from parameters
   - Tests bit 7 of info1 (at 0x0AAE in CODE 27 pre-processing)
   - If bit 7 set: sends info bytes to server as protocol message
   - If bit 7 clear: dispatches through 145-entry jump table at 0x23D0

### Server-Bound Path (bit 7 set)

CODE 27:0x0AB6 -- When info1 has bit 7 set:
- Packs each info byte as 0x01XX words (high byte = 0x01)
- Concatenates into a protocol message via Libs:0x4DFC
- Copies to form output buffer (-$12E from form context)
- Server receives the 3 info bytes and responds with appropriate form

## Known Action Codes

### Local Dispatch Table (info1 bit 7 clear, CODE 4:0x23D0)

| info1 | Dec | Handler | Action | Notes |
|-------|-----|---------|--------|-------|
| $01 | 1 | 0x24F2 | Unknown action 1 | |
| $02 | 2 | 0x2538 | Unknown action 2 | |
| $05 | 5 | 0x2566 | Close/cleanup | |
| $09 | 9 | 0x2594 | Action 9 | |
| $0B | 11 | 0x25A0 | Action 11 | |
| $0D | 13 | 0x25BE | Action 13 | |
| $0E | 14 | 0x25C8 | **Sign On sequence** | Checks free RAM, calls Schedule:0x33C4 |
| $0F | 15 | 0x25FE | Close forms + mail flag | Post-authentication cleanup |
| $11 | 17 | 0x2656 | Action 17 | Switch 30 check; may remap to $0B |
| $13 | 19 | 0x2694 | Action 19 | Switch 30 check; may remap to $3F |
| $16 | 22 | 0x26C2 | **Token request** | Reads form fields, sends token to server |
| $17 | 23 | 0x2758 | **Record request** | Reads form fields (DB + rec), sends to server |
| $18 | 24 | 0x27DC | Drawing action | Calls Drawing:0x3528 with d6, d7 |
| $19 | 25 | 0x27E8 | Action 25 | |
| $1E | 30 | 0x280A | Action 30 | |
| $2C | 44 | 0x28A0 | Action 44 | |
| $50 | 80 | 0x2B2A | Action 80 | |

Many entries (0x07, 0x08, 0x0A, 0x10, 0x12, 0x14, 0x15, 0x1A, 0x1C-0x2B,
0x2E-0x30, 0x23-0x2B, etc.) jump to exit (0x2EEC = no-op).

### Server-Bound Codes (info1 bit 7 set)

| info1 | Lower 7 bits | Used By |
|-------|-------------|---------|
| $8E | $0E (14) | Sign-on form load trigger |

When bit 7 is set, the client sends the info bytes to the server as a
protocol message. The lower 7 bits have meaning to the server, not the
client. The server responds with the appropriate FDO88 form via AT token.

## Canned Form Examples

### Sign On Button (`info=0E0000`)
```
fdo$dispch invoke_record info=0E0000
```
- info1=$0E, info2=$00, info3=$00
- Bit 7 clear -> local dispatch to action 14
- Handler at 0x25C8: checks free RAM >= 320KB, triggers Schedule:0x33C4
- This starts the sign-on authentication sequence

### Post-Auth Form Load (`info=8E0000`)
```
fdo$dispch invoke_record info=8E0000
```
- info1=$8E, info2=$00, info3=$00
- Bit 7 set -> sends to server
- Server receives action $0E and sends back the sign-on form

### XprtX REC# Button (`info=170000`)
```
fdo$dispch invoke_record info=170000
```
- info1=$17, info2=$00, info3=$00
- Bit 7 clear -> local dispatch to action 23
- Handler at 0x2758: reads DB number from field $D4, record ID from field $D5
- Encodes as `(DB * 65536) + recordID`, base-63 encodes, sends to server
- Server responds with that specific DB record's FDO88 data

### XprtX Token Button (`info=160000`)
```
fdo$dispch invoke_record info=160000
```
- info1=$16, info2=$00, info3=$00
- Bit 7 clear -> local dispatch to action 22
- Handler at 0x26C2: reads token from field $D4, value from field $D5
- Sends token request to server

## Loading DB16:252 (Welcome Screen) From Server

invoke_record CANNOT be used to load arbitrary DB forms by type and ID.
The server delivers the Welcome Screen by sending FDO88 form data directly:

1. Send FDO88 data via AT token (0x4154) with 2-byte stream ID
2. Use raw FDO88 binary from DB16 resource ID 252 in Online Database
3. Split at fdo$break boundaries, each chunk in separate AT frame
4. Include fdo$Switch CloseSignOn (switch 87) to dismiss sign-on screen

The client never requests DB16:252 by name. The server sends it as part
of the post-authentication welcome sequence.

## Can the Server Trigger invoke_record Remotely?

No. invoke_record is a client-side button dispatch mechanism. The dispatch
record lives on form elements and is triggered by user clicks.

The server CAN:
- Send any FDO88 form directly via AT token (no invoke_record needed)
- Use low-bit opcode $28 (LoadFormFromDB, CODE 21:0x2F0C) which loads
  from the client's local Online Database file -- but requires the DB
  resource to exist locally on the client
- Use fdo$canned (opcode $01/$81) to reference canned forms within the
  current form stream during form creation

## CODE 14 (Dbase) DB Resource Lookup

For reference, the function at CODE 14:0x02D8 resolves a word value to
a DB resource type and record ID. This is used internally but NOT by
invoke_record for arbitrary DB lookups:

```
Input: word value at $8(a6)
If value < 256: no resource (exit)
DB_number = (value / 256) + 16
Record_ID = (value % 256) + global_shift
Resource type = "DB" + hex(DB_number)  e.g., DB16, DB1A, etc.
Call GetResource("DBxx", Record_ID)
```

Range: DB_number 0..10 maps to resource types DB10..DB1A.
This means only DB16 through DB26 (decimal) are addressable: DB10-DB1A.

## Key Code Locations

| Location | Function |
|----------|----------|
| CODE 27:0x04C4 | Button click handler |
| CODE 27:0x0450 | Extract dispatch info from element |
| CODE 27:0x02FE | Dispatch processor (send + post event) |
| CODE 27:0x206C | Event handler (MOP dispatch) |
| CODE 27:0x2250 | MOP jump table (49 entries) |
| CODE 27:0x2636 | MOP $24 (invoke_record) handler |
| CODE 27:0x0AAE | Bit 7 check for local vs remote |
| CODE 27:0x0AB6 | Server-bound message builder |
| CODE 4:0x22DC | invoke_record event handler |
| CODE 4:0x23D0 | Action dispatch table (145 entries) |
| CODE 4:0x25C8 | Action $0E: Sign On |
| CODE 4:0x26C2 | Action $16: Token request |
| CODE 4:0x2758 | Action $17: Record request |
| CODE 4:0x2272 | Record request encoder (base-63) |
| CODE 14:0x01DE | Dispatch info parser |
| CODE 14:0x02D8 | DB resource type resolver |
