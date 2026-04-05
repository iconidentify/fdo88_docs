# AOL 2.7 Mac Client - Connection Flow Analysis

Reconstructed from disassembly of the AOL 2.7 client binary (851KB, 57 CODE segments),
171 canned FDO88 forms from the Online Database, the FDO88 Manual, and P3 protocol documentation.

## Client Architecture

The AOL 2.7 Mac client is a 68k Macintosh application organized into 57 CODE segments
totaling 721KB of executable code:

```
CODE  0  (13KB)  [Jump table - segment loader]
CODE  1  (42KB)  Main              - Application entry, main event loop
CODE  2  (20KB)  InitUnit          - Startup initialization, globals setup
CODE  3  (31KB)  Libs              - Shared library routines
CODE  4  (27KB)  Events            - Event dispatch, idle processing
CODE  5  (23KB)  P3                - P3 protocol: framing, CRC, sequencing
CODE  6  (27KB)  DataParsing       - FDO88 atom stream decoder (the binary parser)
CODE  7  (21KB)  ToolkitUtils      - Online Tool loading and management
CODE  8  (19KB)  Toolkit           - Tool API framework
CODE  9  ( 4KB)  TokenHandler      - Routes P3 tokens to handlers
CODE 10  (18KB)  FormsInfo         - FDO88 form metadata and state tracking
CODE 11  (14KB)  Drawing           - Mac QuickDraw rendering of forms
CODE 12  (28KB)  FormModifiers     - FDO88 opcode interpreter (executes commands)
CODE 13  (26KB)  CCL               - Connection Control Language (modem scripts)
CODE 14  ( 2KB)  Dbase             - Local database (canned forms, main.idx)
CODE 15  ( 3KB)  Dialogs           - Alert/dialog management
CODE 16  ( 1KB)  Utils             - Misc utilities
CODE 17  (17KB)  SerStuff          - Serial port / modem I/O
CODE 18  ( 5KB)  Printing          - Print support
CODE 19  ( 2KB)  WindowUtes        - Window utilities
CODE 20  ( 3KB)  FormsDeletion     - Form teardown and cleanup
CODE 21  (28KB)  FormsCreation     - Window/field creation from FDO88 commands
CODE 22  (18KB)  Menus             - Menu bar construction and dispatch
CODE 23  (20KB)  Schedule          - Background task scheduling
CODE 24  ( 9KB)  UDO               - User Data Objects
CODE 25  (24KB)  ToolCallbacks     - Callback handlers for Online Tools
CODE 26  (10KB)  EditStuff         - Text editing (TextEdit integration)
CODE 27  (11KB)  MOPs              - Menu Operation (dispatch) execution
CODE 28  (14KB)  DiskIO            - File system operations
CODE 29  ( 6KB)  SoundUtil         - Sound playback (fdo$Sound, fdo$Note)
CODE 30-50 (various) 2D_ENGINE, BAR_ENGINE, PIE_ENGINE, etc. - Charting/graphing
```

## Connection Sequence

### Phase 1: Application Launch

```
InitUnit -> Main -> Events loop
```

1. **CODE 0** (jump table): The Macintosh Segment Loader resolves CODE resource
   references. CODE 0 contains the inter-segment jump table.

2. **CODE 2 (InitUnit)**: Initializes global data structures at offset
   `-0x5356(A5)` (the P3 state block). Sets up the A5 globals world.
   Loads the jump table relocations from the `_DATA` init block.

3. **CODE 14 (Dbase)**: Opens the **Online Database** resource file (the file
   containing DB08-DB16 canned FDO88 forms). The Dbase segment uses Mac
   Resource Manager traps (`_GetResource` = $A9A0, `_LoadResource` = $A9A4,
   `_SizeRsrc` = $A9A3) to load DB resources by type and ID.

4. **CODE 1 (Main)**: Enters the main event loop. Displays the offline
   splash/setup screen from canned forms.

### Phase 2: Modem Dialing & TCP Connection

```
CCL -> SerStuff -> P3 init
```

5. **CODE 13 (CCL)**: The Connection Control Language interpreter runs the
   modem script for the selected access number. CCL scripts are stored in
   the `Online Files/` directory (one per modem model -- Hayes, US Robotics,
   Global Village, etc.). The script sends AT commands, dials the number,
   and waits for CONNECT.

6. **CODE 17 (SerStuff)**: Manages the serial port. Uses a 20KB
   `SERi` resource as the serial input ring buffer. Handles baud rate
   negotiation (300-28800 baud via the modem scripts).

7. **TCP/IP path**: For TCP connections (AOL 2.7 added TCP support), the
   `TCP Connection` and `TCPack` tools handle the socket layer. Connection
   target: `AmericaOnline.aol.com` port **5190** (DNS round-robin).

### Phase 3: P3 Protocol Handshake

```
P3: INIT -> SS/SSR -> Authenticated DATA flow
```

8. **CODE 5 (P3)**: The P3 protocol engine. The first function at offset
   0x04 is the P3 packet builder:

   ```asm
   link.w  a6, #0
   lea.l   -0x5356(a5), a3    ; P3 state block (global)
   movea.l 0x8(a6), a4        ; packet buffer parameter
   moveq   #0, d0
   move.b  (a4), d0           ; read packet type byte
   cmpi.b  #0x1f, d0          ; clamp to max 31
   bls.b   continue
   move.b  #0x1f, (a4)        ; enforce max
   ```

   P3 packet structure (from the protocol spec):
   ```
   [5A]        Sync byte 'Z'
   [CRC hi]    CRC-16 high byte (or '**' for post-3.0)
   [CRC lo]    CRC-16 low byte
   [00]        Padding
   [length]    Payload length
   [tx_seq]    Transmit sequence number
   [rx_seq]    Receive sequence number
   [space]     0x20
   [token hi]  Token identifier high byte
   [token lo]  Token identifier low byte
   [data...]   FDO88 atom stream payload
   ```

   **P3 Handshake**:
   - Client sends **INIT** packet (type `$23`) with client version info
   - Server responds with **SS** (type `$21`)
   - Client sends **SSR** (type `$22`) with authentication
   - Server sends **ACK** (type `$24`)
   - Bidirectional **DATA** (type `$20`) flow begins, carrying FDO88 streams

   The P3 state block at A5-0x5356 tracks:
   - Current tx/rx sequence counters
   - Connection state (disconnected/handshaking/connected)
   - Heartbeat timer (type `$26` -- line-drop detection)
   - Maximum payload size: **119 bytes** per P3 DATA packet

### Phase 4: Authentication & Sign-On

```
P3 DATA -> TokenHandler -> canned sign-on forms
```

9. **CODE 9 (TokenHandler)**: Routes incoming P3 DATA packets by their
   2-byte token identifier:

   ```asm
   link.w  a6, #0
   movea.l 0xc(a6), a2        ; output status pointer
   movea.l 0x10(a6), a3       ; output type pointer
   move.l  0x14(a6), d6       ; data length
   movea.l 0x18(a6), a4       ; data buffer
   clr.b   (a3)               ; clear type
   clr.b   (a2)               ; clear status
   move.l  a4, d0
   beq.b   done               ; null buffer -> done
   tst.l   d6
   ble.b   done               ; zero length -> done
   move.b  (a4), d0           ; first byte = token length indicator
   cmpi.w  #2, d7             ; if <= 2 bytes, short token
   ble.b   short_token
   ; long token: bytes 1-2 are token, compute hash
   move.b  1(a4), d0          ; token high byte
   asl.l   #8, d0             ; shift left 8
   move.b  2(a4), d1          ; token low byte
   move.w  d1, d5
   add.w   d0, d5             ; d5 = full token value
   ```

   Common tokens and their handlers:
   | Token | Meaning | Handler |
   |-------|---------|---------|
   | `at`  | FDO88 atom stream (4-byte stream ID) | FormsInfo -> DataParsing |
   | `At`  | FDO88 atom stream (3-byte stream ID) | FormsInfo -> DataParsing |
   | `Ki`  | Keyboard input response | Events |
   | `f1`  | File transfer data | ToolCallbacks |
   | `SC`  | Sign-on/setup cluster | FormsCreation |

10. The server sends the **sign-on form** as an `at` or `At` token
    containing an FDO88 stream. If the client is offline, it loads the
    sign-on screen from local canned forms:

    **DB14 ID:161** - Sign-On Screen:
    ```
    fdo$start
    fdo$Window16 center center 500 290 normal
    fdo$SetWindowTag cluster:OF id=4
    fdo$Title "AOL Setup & Sign On"
    fdo$Field16 Text ...          ; screen name label
    fdo$Field16 Popup ...         ; screen name dropdown
    fdo$Field16 Text ...          ; password label  
    fdo$Field16 Text ... editable ; password field (max 8 chars)
    fdo$Field16 Button ... "Sign On"
      fdo$dispch invoke_record    ; triggers sign-on sequence
    fdo$Field16 Button ... "Setup"
      fdo$dispch mop_$28          ; opens setup wizard
    fdo$enddef
    ```

### Phase 5: FDO88 Stream Processing

```
TokenHandler -> FormsInfo -> DataParsing -> FormModifiers -> FormsCreation -> Drawing
```

11. **CODE 10 (FormsInfo)**: Manages the form state machine. When a new
    FDO88 stream arrives:

    ```asm
    ; FormsInfo entry - process incoming atom stream
    tst.l   -0x4e98(a5)       ; check form context pointer
    beq.b   no_context
    movea.l -0x4e98(a5), a0   ; load form context
    tst.l   (a0)              ; is it valid?
    bne.b   process
    ```

    FormsInfo tracks:
    - Active form context (window being built)
    - Field counter (sequential field numbering)
    - Stream continuation state (for multi-packet forms using `fdo$break`)

12. **CODE 6 (DataParsing)**: The **FDO88 binary decoder**. This is our
    decoder's real-world counterpart. It reads the binary stream byte by
    byte, applying the encoding rules we reverse-engineered:

    ```asm
    ; DataParsing - read next opcode
    link.w  a6, #-0x12
    movea.l 0x8(a6), a4       ; stream buffer
    jsr     validate(pc)       ; check stream header
    tst.b   d0
    beq.b   error              ; invalid stream
    moveq   #0, d6             ; byte offset = 0
    ; main decode loop
    loop:
      pea.l  -0x12(a6)        ; local frame buffer
      move.l 0xc(a6), d0      ; total length
      sub.l  d6, d0            ; remaining bytes
      pea.l  (a4, d6.l)       ; current position in stream
      jsr    decode_atom(pc)   ; decode next atom
    ```

    The `decode_atom` subroutine implements the same logic our Java decoder uses:
    - Check high bit for byte-count vs fixed params
    - Handle $F8 extended prefix
    - Route each decoded opcode to FormModifiers

13. **CODE 12 (FormModifiers)**: The **FDO88 opcode interpreter**. Each
    decoded command is dispatched here. The first function reads the opcode
    byte and handles the high-bit / value-range mapping:

    ```asm
    ; FormModifiers - read opcode byte from stream
    movea.l 0xc(a4), a0       ; stream read pointer
    move.b  (a0), d0          ; read opcode byte
    ext.w   d0                ; sign-extend
    move.w  d0, d7
    bge.b   positive
    add.w   #0x100, d7        ; handle negative (unsigned 0x80-0xFF)
    positive:
    addq.l  #1, 0xc(a4)       ; advance read pointer
    ```

    The second function accumulates stream data into a buffer, enforcing
    the 255-byte maximum field size:

    ```asm
    addq.w  #1, -2(a4)        ; increment byte counter
    cmpi.w  #0xff, -2(a4)     ; check max 255
    ble.b   ok
    move.w  #0xff, -2(a4)     ; clamp to 255
    ```

14. **CODE 21 (FormsCreation)**: Converts decoded FDO88 commands into
    actual Macintosh windows and controls:
    - `fdo$Window16` / `fdo$window` -> Mac `_NewWindow` / `_NewCWindow` traps
    - `fdo$Field16` -> creates text fields, buttons, lists, popups
    - `fdo$Picture` / `fdo$MacIcon` -> draws PICT/ICON resources
    - `fdo$Title` -> calls `_SetWTitle`
    - `fdo$SetFont` -> calls `_TextFont` / `_TextSize`

### Phase 6: Welcome Screen

```
Server sends Welcome form -> client renders it
```

15. After successful authentication, the server sends the **Welcome Screen**
    as a host form (FDO88 stream over P3). The client also has a local
    fallback in the Online Database:

    **DB16 ID:252** - Welcome Screen:
    ```
    fdo$start
    fdo$Window16 center center 444 280 type_9
    fdo$break
    fdo$SetWindowTag cluster:ON id=1
    fdo$PlusGroup ...
    fdo$Switch SetUntitledStr
    fdo$Title "Welcome"
    fdo$Picture resid=1822 at 5,0         ; Welcome banner art
    fdo$dispch no_action
    fdo$Picture resid=1232 at 70,248      ; artwork
    fdo$Mark field=3 mark=41
    fdo$dispch invoke_and_send
    fdo$Switch SetToolDispch
    fdo$TextDesc application 10pt plain black
    fdo$Field16 Text 150 7 215 60 scrollable
    fdo$Switch SetToolDispch
    ; ... (spotlight buttons, post office, discover AOL, etc.)
    fdo$SndName "Welcome"                 ; plays the iconic "Welcome!" sound
    fdo$enddef
    ```

    **DB16 ID:251** - Main Menu:
    ```
    fdo$start
    fdo$Switch SetToolDispch
    fdo$Window16 center center 500 290 type_22
    fdo$Title "Main Menu"
    fdo$Field16 Text ...                  ; "IN THE SPOTLIGHT"
    fdo$Picture ...                       ; spotlight artwork
    fdo$Field16 Text ...                  ; "POST OFFICE"
    fdo$Picture ...                       ; post office icon
    fdo$Field16 Text ...                  ; "DISCOVER AOL"
    ; ... (14 department buttons with dispatch actions)
    fdo$enddef
    ```

### Phase 7: Dispatch Loop

```
User clicks -> Events -> MOPs -> P3 token -> Server response -> new form
```

16. **CODE 27 (MOPs)**: When a user clicks a button or selects a list item,
    the associated **dispatch** fires. The dispatch is a 6-byte structure
    (from the glossary: "Six-byte set of parameters"):

    ```
    [MOP code]     1 byte  - Menu Operation code
    [token hi]     1 byte  - P3 token identifier
    [token lo]     1 byte  - P3 token identifier  
    [info byte 1]  1 byte  - MOP-specific data
    [info byte 2]  1 byte  - MOP-specific data
    [info byte 3]  1 byte  - MOP-specific data
    ```

    Common MOP codes:
    | MOP | Name | Action |
    |-----|------|--------|
    | $00 | none | No action |
    | $05 | close | Close current form |
    | $12 | send_form | Send field data to host via P3 |
    | $13 | send_selected | Send selected list item |
    | $24 | invoke_record | Load a canned form from local DB |
    | $26 | invoke_and_send | Load form AND send data |
    | $27 | ask_indirect | Indirect form request |
    | $80 | no_action | Placeholder |
    | $81 | goto_keyword | Navigate to AOL keyword |
    | $89 | run_tool | Launch an Online Tool |
    | $8A | open_room | Enter a chat room |
    | $90 | goto_url | Open an aol:// or http:// URL |

    The MOP executor in CODE 27 reads the 6-byte dispatch, sends the
    appropriate P3 token to the server, and the server responds with
    a new FDO88 stream to render.

## Data Flow Summary

```
                    AOL 2.7 Mac Client
                    ==================

  [Modem/TCP] <---> [SerStuff/TCPack]
                         |
                    [P3 Protocol]     <- CODE 5: framing, CRC, seq numbers
                         |
                    [TokenHandler]    <- CODE 9: routes by 2-byte token
                         |
              +----------+----------+
              |                     |
         [FormsInfo]           [ToolCallbacks]
         CODE 10                CODE 25
              |                     |
         [DataParsing]         [Online Tools]
         CODE 6: FDO88             (Chat, Mail,
         binary decoder             File Transfer)
              |
         [FormModifiers]
         CODE 12: opcode
         interpreter
              |
    +---------+---------+
    |         |         |
[FormsCreation] [Drawing] [Menus]
  CODE 21      CODE 11   CODE 22
  Mac windows  QuickDraw  Menu bar
  and fields   rendering  construction
    |
[MOPs] <- CODE 27: dispatch execution
    |
  [P3] -> sends token to server -> server responds with new FDO88 stream
```

## Key Findings

1. **DataParsing (CODE 6)** is our decoder's real-world counterpart -- 27KB of
   68k assembly that implements the same high-bit/low-bit/extended opcode
   logic we reverse-engineered.

2. **FormModifiers (CODE 12)** is the opcode interpreter -- 28KB that reads
   each decoded command and calls FormsCreation to build Mac UI elements.
   This is the segment AOL4Free patches to skip billing enforcement.

3. **TokenHandler (CODE 9)** is the router -- it reads the 2-byte token from
   each P3 DATA packet and dispatches to the appropriate handler. FDO88
   streams arrive as `at` or `At` tokens.

4. **The P3 state block** lives at A5-0x5356, a fixed offset in the A5 globals
   world. All P3 functions reference this address. The state block contains
   connection status, sequence counters, and the 119-byte payload buffer.

5. **Canned forms** in the Online Database serve as **offline UI** -- the
   sign-on screen, setup wizard, and error dialogs are all local FDO88
   forms loaded via CODE 14 (Dbase) using Mac Resource Manager calls.
   Host forms (sent by the server) are dynamic content that arrives
   over P3 during a session.
