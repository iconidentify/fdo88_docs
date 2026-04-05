# Dialtone AOL 2.7 Mac Client Support - Protocol Reference

Extracted from disassembly of the AOL 2.7 client binary (851KB, 57 CODE segments),
171 canned FDO88 forms, 42 string tables, and cross-referenced with Dialtone's
existing AOL 3.0 implementation.

## Client Identification

```
Version:   2.7 (vers resource: v2.112)
Copyright: 1987-1996 America Online, Inc.
Platform:  Macintosh (68k)
Serial ID: "A-OL" (STR# 10011)
TCP ID:    "TCPa" (STR# 1300)
```

The client identifies via the INIT packet's platform byte. Dialtone's `InitPacketParser`
already supports Tier 1 (6-byte) parsing for Mac clients. Check `platform >= 127` or
`platform == 2` for Mac detection.

## Token Map (from CODE 9 TokenHandler disassembly)

### Tokens the Client Handles (Server -> Client)

| Token | Hex | Handler | Purpose |
|-------|------|---------|---------|
| `wS` | 0x7753 | Window Show | Show/activate a window by ID |
| `wC` | 0x7743 | Window Close | Close a window by ID |
| `wH` | 0x7748 | Window Hide | Hide a window (keep state) |
| `hS` | 0x6853 | Host String | Display a host-sent string message |
| `hV` | 0x6856 | Host Value | Set a host variable value |
| `hO` | 0x684F | Host Open | Open a host-specified form/window |
| `AF` | 0x4146 | Add Form | Add/create a new form (flag=1) |
| `RF` | 0x5246 | Return Form | Return/update existing form (flag=0) |
| `EW` | 0x4557 | Error Warning | Display warning to user |
| `EC` | 0x4543 | Error Critical | Display critical error |
| `OT` | 0x4F54 | Online Tools | Tool management command |
| `ya` | 0x7961 | Y-command A | Part of ya-ye series (5 tokens) |
| `yb` | 0x7962 | Y-command B | Y-command series |
| `yc` | 0x7963 | Y-command C | Y-command series |
| `yd` | 0x7964 | Y-command D | Y-command series |
| `ye` | 0x7965 | Y-command E | Y-command series |
| `ur` | 0x7572 | URL | Handle URL navigation |

### Token Dispatch Logic

```
if token < 0x2000:
    // Low tokens: parse as FDO88 atom stream
    // Extract stream ID from payload
    // Feed to DataParsing -> FormModifiers -> FormsCreation
else:
    // High tokens: check ya-ye series first (0x7961-0x7965)
    // Then check ur (0x7572)
    // Then cascade through: wS/wC/wH -> hS/hV/hO -> AF/RF -> EW/EC/OT
    // Finally: default handler at jsr 0x131a(a5)
```

### Key Token Differences from AOL 3.0

Dialtone currently uses these tokens for AOL 3.0:

| 3.0 Token | 2.7 Equivalent | Notes |
|-----------|----------------|-------|
| `AT` | `AF`/`RF` | 2.7 distinguishes Add vs Return forms |
| `ff` | Likely same | Login/handshake |
| `fh` | `hO` | Form/DOD request |
| `Kk` | Not found in 2.7 | Keywords may use different token |
| `pE` | Likely same | Logout |
| `St` | Via Online Tool (Mail) | IM send goes through Mail tool |

## Online Tool Token Registry

Extracted from `Ttkn` resources in each Online Tool's resource fork.
These are the P3 tokens each tool registers to handle:

### Members Tool (ID=4138) -- Handles Instant Messages
| Token | Hex | Purpose |
|-------|------|---------|
| `iP` | 0x6950 | IM present/probe |
| `iT` | 0x6954 | IM text (message body) |
| `iE` | 0x6945 | IM event (typing, etc.) |
| `iA` | 0x6941 | IM action (send/receive) |
| `iB` | 0x6942 | IM buddy status |

Strings: `"Instant Message from ^1"`, `"Instant Message"`,
`"You can't send an empty Instant Message."`, `"\r^1: "` (message prefix)

### Chat Tool (ID=4134) -- Handles Chat Rooms
| Token | Hex | Purpose |
|-------|------|---------|
| `AA` | 0x4141 | Chat action A |
| `AB` | 0x4142 | Chat action B |
| `AC` | 0x4143 | Chat action C |
| `AD` | 0x4144 | Chat action D |
| `AX` | 0x4158 | Chat extended |
| `CA` | 0x4341 | Chat room A (enter/create) |
| `CB` | 0x4342 | Chat room B (leave/close) |
| `CF` | 0x4346 | Chat room F (configure) |
| `c@` | 0x6340 | Chat at (message) |
| `cY` | 0x6359 | Chat Y |
| `rD` | 0x7244 | Room data |
| `aa` | 0x6161 | Chat action lowercase |
| `Ab` | 0x4162 | Chat action b |
| `Ac` | 0x4163 | Chat action c |
| `Ca` | 0x4361 | Chat room a |
| `Cf` | 0x4366 | Chat room f |

Strings: `"People Connection"`, `"^1 - Hilited"`, `"^1 - Ignored"`,
`" : "` (message separator), `"^1, ^2"` (member list join)

### Mail Tool (ID=4133) -- Handles Email
| Token | Hex | Purpose |
|-------|------|---------|
| `mB` | 0x6D42 | Mail box operations |
| `mT` | 0x6D54 | Mail transfer |

Strings: Field headers `"From:  "`, `"Subj:  "`, `"To:  "`, `"cc:  "`,
`"bcc:  "`, `"Date:  "`, `"File:  "`. Prefixes: `"Re:"`, `"Fwd:"`.
Forward separator: `"\r\r--------------\rForwarded Message:\r\r"`

### File Transfer Tool (ID=4144) -- Handles Downloads/Uploads
| Token | Hex | Purpose |
|-------|------|---------|
| `ta` | 0x7461 | Transfer action |
| `th` | 0x7468 | Transfer header |
| `tf` | 0x7466 | Transfer file |
| `td` | 0x7464 | Transfer data |
| `tc` | 0x7463 | Transfer complete |
| `F7` | 0x4637 | File 7 |
| `FF` | 0x4646 | File finish |
| `F8` | 0x4638 | File 8 |
| `F9` | 0x4639 | File 9 |
| `FM` | 0x464D | File manager |
| `FK` | 0x464B | File kill |
| `fX` | 0x6658 | File extended |
| `TA` | 0x5441 | Transfer ack |
| `ti` | 0x7469 | Transfer info |
| `tj` | 0x746A | Transfer join |
| `t1` | 0x7431 | Transfer 1 |
| `t2` | 0x7432 | Transfer 2 |
| `t3` | 0x7433 | Transfer 3 |
| `tT` | 0x7454 | Transfer type |
| `tN` | 0x744E | Transfer name |
| `fx` | 0x6678 | File transfer X |

### Goto Tool (ID=4130) -- Handles Keywords
No registered tokens (keywords go through MOPs, not direct tokens).

Default favorites (STR# 4130): "New Services", "Discover America Online",
"Sign on a Friend", "Top News", "Stock Quotes", "Center Stage",
"Internet Connection" + 4 user-customizable slots.

## Instant Messages

**Correction**: IMs are handled by the **Members Tool** (ID=4138), not Mail.
The Members tool registers 5 IM-specific tokens (`iP`, `iT`, `iE`, `iA`, `iB`).

1. **Sending**: User types message in IM window (canned form DB15 ID:170/171/172)
   - The IM window has fields: "Talk to:" (screen name), "Type your message:" (text)
   - Buttons: "Send", "Reply", "Get Profile", "Locate"
   - Send button dispatch: `invoke_and_send` (MOP $26) -- sends field data to host
   - Members tool sends via `iA` (IM action) token to host

2. **Receiving**: Host sends `iT` (IM text) token with sender + message
   - Members tool creates an IM window with title `"Instant Message from ^1"`
   - Message formatted as `"\r^1: "` + message text

3. **Window types** (from canned forms):
   - DB15 ID:170 -- IM window (basic)
   - DB15 ID:171 -- IM window (with reply)
   - DB15 ID:172 -- IM window (full featured, with profile/locate)

4. **P3 token flow**:
   ```
   Client sends: [token for Mail tool] + [recipient screen name] + [message text]
   Server sends: [token for Mail tool] + [sender screen name] + [message text]
   ```
   The actual token is routed through the Online Tool framework, not a direct fixed token.

## Chat Rooms

Chat is handled by the **Chat Online Tool** (Online Tools/Chat).

1. **Entering a room**: Via dispatch `open_room` (MOP $8A) or keyword
   - The `fdo$dispch open_room token=".X"` dispatch sends a room name to the host
   - Host responds with chat room FDO88 form

2. **Chat window structure** (from canned form DB13 ID:13):
   ```
   fdo$Window16 ...
   fdo$Field16 List ...        ; member list (who's in room)
   fdo$Field16 Text ...        ; chat log (scrolling text area)
   fdo$Field16 Text editable   ; input field (type here)
   fdo$Field16 Button "Send"   ; send button
   ```

3. **Chat message flow**:
   ```
   Client: [chat token] + [message text]
   Server: [chat token] + [sender:message] broadcast to all room members
   ```

4. **Chat-specific strings** (STR# 10018):
   - `"/<chatN"` reference in FormsCreation indicates chat room naming pattern

5. **Chat room types** (from DB14 forms):
   - Public rooms: opened by keyword
   - Private rooms: opened by name (see XprtX form: "To create or enter a private room...")
   - Conference rooms: special room type
   - Guide rooms: internal AOL staff rooms (Secret Guide Room "Center of the Earth")

## Keywords

Keywords are the primary navigation mechanism in AOL 2.7.

1. **Keyword dispatch**: User enters keyword via Go To menu or Ctrl+K
   - Goes through **MOPs** (CODE 27)
   - MOP code `$81` = `goto_keyword`
   - The keyword string is sent to the host as a P3 token

2. **Host response**: Server looks up the keyword and responds with:
   - An FDO88 form to render (the keyword's landing page)
   - Or a redirect to another area/form

3. **Free Area keywords** (from STR# 10026):
   - "Exit Free Area" (switch between billed/free)
   - "Sign Off"
   - "Set Up & Sign On"

4. **Keyword-related strings** (STR# 10018):
   - `"File"`, `"Go To"`, `"Post Office"`, `"People"` -- main menu categories

## MOP (Menu Operation) Codes

From CODE 27 disassembly and cross-reference with FDO88 manual:

| MOP | Name | Action | Dialtone Equivalent |
|-----|------|--------|---------------------|
| $00 | none | No action | Same |
| $05 | close | Close current form | Same |
| $11 | type_17 | Internal (from MOPs.bin) | -- |
| $12 | send_form | Send all field data to host | Same |
| $13 | send_selected | Send selected list item | Same |
| $15 | type_21 | Internal | -- |
| $19 | type_25 | Internal | -- |
| $24 | invoke_record | Load canned form from local DB | Same |
| $26 | invoke_and_send | Load form AND send data | Same |
| $27 | ask_indirect | Indirect form request | Same |
| $28 | setup_wizard | Opens setup (from sign-on screen) | -- |
| $30 | type_48 | Internal | -- |
| $80 | no_action | Placeholder | Same |
| $81 | goto_keyword | Navigate to keyword | Same |
| $83 | tool_command | Send command to Online Tool | -- |
| $89 | run_tool | Launch Online Tool | Same |
| $8A | open_room | Enter chat room | Same |
| $90 | goto_url | Open URL (aol:// or http://) | Same |

## Login / Sign-On Flow (Critical Path for Dialtone)

Traced from CODE 2 (InitUnit), CODE 1 (Main), CODE 27 (MOPs), and the sign-on
form DB14:161. Cross-referenced with Dialtone's existing AOL 3.0 LoginTokenHandler.

### Q: What token carries credentials after the user clicks "Sign On"?

**`Dd` -- same as AOL 3.0.** The sign-on form's "Sign On" button fires MOP `$24`
(invoke_record) with info `0E 00 00`, which triggers the sign-on procedure in
InitUnit (CODE 2). InitUnit builds the credentials as an FDO atom stream with
`de_data` atoms (screen name + password) and sends it as a P3 DATA packet with
token `Dd`.

The credential payload format is identical to what Dialtone already handles via
`FdoStreamExtractor.extractLoginCredentials()`:

```
P3 DATA frame:
  [5A] [CRC] [LEN] [TX] [RX] [20] [Dd] [stream_id]
  FDO payload:
    de_data <screen_name>
    de_data <password>
```

**Important:** The 2.7 client uses FDO88 binary encoding for the outbound `de_data`
atoms (high-bit byte-count format), but the de_data content is just strings.
Dialtone needs to handle FDO88 atom stream decoding for the Dd frame, not just FDO91.
The `atomforge-fdo` library's `Fdo88Decoder` handles this.

### Q: Does the client send a "ready" signal before receiving the Welcome screen?

**No.** The server pushes immediately after successful authentication. The complete
sequence from disassembly:

```
1. TCP connect to AmericaOnline.aol.com:5190
2. Client -> Server: P3 INIT packet (0xA3)
     Contains: platform=2 (Mac), version=2.7, memory info
     String evidence: "P3:Sending InitPacket" in InitUnit
3. Server -> Client: P3 handshake (SS/SSR exchange)
4. Client -> Server: Dd token with FDO stream
     Contains: de_data[screen_name] + de_data[password]
5. Server -> Client: (one of)
     Success: Welcome screen form via AF/RF token
     Failure: Error form via EW token
       STR# 10030[0]: "Invalid account number or password."
       STR# 10030[1]: "Your account is already signed on."
       STR# 10030[2]: "Host not responding to our Init Message."
```

No intermediate "ready" handshake exists. The Dd frame IS the ready signal --
when the server receives valid credentials, it immediately pushes the Welcome
screen. This matches AOL 3.0 behavior.

### Q: What is the SC token's role in the login sequence?

**SC is NOT a P3 token.** It is a window cluster identifier (0x5343 = ASCII "SC")
used with `fdo$SetWindowTag` and `fdo$UseDisplay` to group Setup/Configuration
windows together.

Window clusters in the sign-on flow:
- `OF` (0x4F46) -- Offline cluster. The sign-on form uses `windowTag("OF", 4)`.
  All offline windows belong to this cluster.
- `ON` (0x4F4E) -- Online cluster. The Welcome screen uses `windowTag("ON", 1)`.
  All online windows belong to this cluster.
- `SC` (0x5343) -- Setup cluster. Used by setup wizard screens.

When the user signs on successfully:
1. Client closes all `OF` cluster windows (sign-on screen, setup dialogs)
2. Server sends Welcome screen with `windowTag("ON", 1)`
3. Client opens `ON` cluster windows

SC appears heavily in FormsInfo (CODE 10) because that segment tracks which
windows belong to which cluster. It is purely a local UI organizational concept
with no wire protocol role.

### Sign-On Form Structure (DB14:161)

```
fdo$start
  fdo$Switch switch_81               ; behind-modals flag
  fdo$Window16 ...                    ; main sign-on window
  fdo$SetWindowTag cluster:OF id=4   ; OFFLINE cluster
  fdo$Title "Goodbye From America Online!"
  ...
  fdo$Field16 Popup ...               ; screen name dropdown
    fdo$Mark field=0 mark=48640       ; mark for screen name retrieval
  fdo$Text "Password: "
  fdo$Field16 Text editable+sendform  ; password field (max 8 chars)
    fdo$Switch 109                    ; password field config
    fdo$Switch 225                    ; password display config
    fdo$Mark field=0 mark=49152       ; mark for password retrieval
  fdo$Field16 Button default          ; "Sign On Again" button
    fdo$dispch invoke_record info=0E0000  ; triggers sign-on procedure
  fdo$Field16 Button                  ; "Setup" button
    fdo$dispch setup_wizard info=00140A
  fdo$Field16 Button                  ; "Help" button
    fdo$dispch goto_keyword
  ...
  fdo$Text "Locality:"
    fdo$Mark field=0 mark=2580        ; locality/access number
    fdo$dispch invoke_record info=8E0000
  ...
fdo$enddef
```

The `sendform` flag on the password field means its data is included when
the sign-on procedure sends the Dd token. The screen name comes from the
Popup field. Both are extracted by mark number from the form's field list.

## P3 Protocol Details

From CODE 5 (P3) and CODE 2 (InitUnit) disassembly:

### Constants
| Constant | Value | Purpose |
|----------|-------|---------|
| P3 state block | A5-0x5356 | Global connection state |
| Buffer size | 0x0270 (624) | P3 buffer allocation |
| Frame size | 0x0276 (630) | Max frame including header |
| Max payload | 0x0080 (128) | Max payload per DATA packet |
| Max sequence | 0xFF (255) | Sequence number range |
| Sync byte | 0x5A ('Z') | Frame sync |

### INIT Packet (Client -> Server)
From CODE 2 InitUnit debug strings:
- `"Trying to send an InitPacket"` -- sent on connection
- `"Sending HBEAT to Host"` -- periodic heartbeat
- `"Sending NAK to Host"` -- negative acknowledgment

### Error States (STR# 10029/10030)
| Error | Message |
|-------|---------|
| Init timeout | "Unable to initialize session. INIT packet was not acknowledged." |
| Packet reflect | "Packet reflection detected. Session has been closed." |
| Heartbeat fail | "Maximum number of heartbeats exceeded. Session has been closed." |
| System packet | "System packet was not acknowledged. Session has been closed." |
| Auth fail | "Invalid account number or password." |
| Already on | "Your account is already signed on." |
| Host timeout | "Host not responding to our Init Message." |

## Switch Values (FormModifiers)

From CODE 12 disassembly and string tables:

| Number | Name | Purpose |
|--------|------|---------|
| 0 | SetUntitledStr | Set untitled window string |
| 2 | SetToolDispch | Route dispatches to tool |
| 10 | FieldBoolean1On | Enable field boolean 1 |
| 44 | SetMajorField | Mark field as major (save target) |
| 50 | FieldBoolean1Off | Disable field boolean 1 |
| 59 | SetToolDisplay | Mark field as tool-owned |
| 63 | SetWarnDisplay | Warn on close with unsaved data |
| 81 | BehindModals | Place window behind modal |
| 88 | SetEnterKeyField | Set enter-key target field |
| 104 | FillLanguageList | Populate language dropdown |
| 109 | (password related) | Password field configuration |
| 115 | AccentsOk | Allow extended ASCII in field |
| 155 | AccentsOff | Disallow extended ASCII |
| 170 | (special display) | Display modifier |
| 200 | (tool callback) | Tool-specific switch |
| 204 | (tool callback) | Tool-specific switch |
| 225 | (password related) | Password field variant |
| 239 | ExitTool | Exit/close the current tool |

## Canned Form Inventory (Online Database)

Critical forms the server should know about:

| DB | ID | Description | When Loaded |
|----|-----|-------------|-------------|
| DB16 | 252 | Welcome Screen | After sign-on |
| DB16 | 251 | Main Menu | After Welcome |
| DB15 | 170-172 | IM Windows (3 variants) | On IM receive/send |
| DB15 | 152 | Update dialog | On update available |
| DB14 | 161 | Sign-On Screen | App launch (offline) |
| DB14 | 163 | Sign-On Screen (variant) | Alt sign-on |
| DB14 | 162 | Welcome art panel | Sign-on screen bg |
| DB14 | 190 | Members menu | Menu bar creation |
| DB14 | 200 | Go To menu | Menu bar creation |
| DB14 | 208 | Chat Prefs menu | Chat tool |
| DB14 | 214 | Chat room list | Entering rooms |
| DB14 | 230-231 | Yes/No dialogs | Confirmations |
| DB13 | 13 | Chat room window | In chat |
| DB13 | 53 | (AOL branded form) | Various |
| DB11 | 200 | Preferences | User settings |
| DB11 | 66 | Voice settings | TTS prefs |
| db08 | various | Setup wizard forms | First run / setup |

## Online Tool Registration

Tools register via `AOtk` resources. The main app loads tools from the `Online Tools/` folder:

| Tool | Purpose | Token Handling |
|------|---------|----------------|
| Chat | Chat rooms, IMs | Chat protocol tokens |
| Mail | Email, IMs, address book | Mail/IM tokens |
| File Transfer | Downloads, uploads | XFER tokens |
| Setup | Account configuration | Local only |
| Members | Member directory | Directory tokens |
| Goto | Keyword navigation | Keyword tokens |
| Compression | StuffIt integration | File decompression |
| Upgrade Tool | Version updates | Update tokens |
| Address Book | Contact management | Local + sync |

## What Dialtone Needs to Change

### 1. Client Detection (InitPacketParser)
- Already supports Mac via Tier 1 parsing
- Add version check: `if major == 2 && minor >= 5` -> AOL 2.x Mac client
- Set `ClientPlatform.MAC` and `fdoVersion = FDO88`

### 2. FDO Format Switching
- When client is detected as 2.x: use `Fdo88Compiler` instead of `FdoCompiler`
- All form responses must be FDO88 binary, not FDO91
- The `FdoProcessor` and `DodRequestHandler` need a format-aware compilation path

### 3. Token Handling
- `AF`/`RF` tokens (Add Form / Return Form) replace `AT` for form delivery
- `hS`/`hV`/`hO` tokens for host string/value/open
- `wS`/`wC`/`wH` for window show/close/hide
- `ya`-`ye` series for Y-commands
- `EW`/`EC` for error display

### 4. Form Library
- Create FDO88 equivalents of the 15 `replace_client_fdo/` forms
- Use the DB resource IDs from the client's Online Database as GID references
- The client's local DB has fallback forms; the server sends host forms that override them

### 5. IM Implementation
- Route through Mail tool token path (not a direct `St`/`IM` token)
- IM window FDO88 forms: DB15 170-172
- Send: `invoke_and_send` MOP with field data
- Receive: server sends FDO88 form with sender + message text

### 6. Chat Implementation
- Route through Chat tool token path
- Chat window: DB13 ID:13
- Room entry via `open_room` MOP ($8A)
- Member list updates via form field modification
- Message broadcast: server sends text to all room members

### 7. Keyword Handling
- Client sends keyword via `goto_keyword` MOP ($81)
- Server looks up keyword -> responds with FDO88 form
- Same concept as AOL 3.0 keywords but different GID numbering

### 8. P3 Compatibility
- Same P3 protocol (framing, CRC, sequencing)
- Mac client may use shorter INIT packet (Tier 1: 6 bytes vs 52 for Windows)
- Heartbeat and ACK behavior should be identical
- Max payload: 128 bytes (client constant 0x0080, slightly larger than 3.0's 119)
