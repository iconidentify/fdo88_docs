# INIT Packet Construction -- Annotated 68k Disassembly

Disassembled from the AOL 2.7 Mac client binary (CODE 5 / P3 protocol engine).
The INIT packet is the first thing the client sends to the server during the P3
handshake. It tells the server what client version, OS, hardware, and connection
method the user has.

Verified against a live wire capture (2026-04-05) via Wiretap.

## Quick 68k Primer

If you've never read 68k assembly, here's what you need:

- **Registers**: D0-D7 are data registers (like variables), A0-A7 are address
  registers (like pointers). A5 holds the application's global variable base.
  A6 is the frame pointer (like `rbp` on x86). A7 is the stack pointer.
- **LINK/UNLK**: `LINK A6, #-N` allocates N bytes of local stack space.
  Local variables live at negative offsets from A6.
- **Addressing**: `-$2710(A5)` means "the byte at address A5 minus 0x2710."
  This is how the Mac Toolbox accesses global variables.
- **MOVE.B/W/L**: Copy a byte (8-bit), word (16-bit), or long (32-bit).
  `MOVE.B D0, -$32(A6)` copies the low byte of D0 into the local at A6-0x32.
- **Traps**: Instructions starting with `$A` are Macintosh Toolbox calls.
  `$A9A0` = _GetResource, `$A02E` = _BlockMoveData, `$A1AD` = _Gestalt.
- **JSR offset(A5)**: Calls a function through the application's jump table.
  This is how segmented Mac apps call between CODE segments.
- **Big-endian**: 68k is big-endian. The word 0x0761 is stored as byte 0x07
  followed by byte 0x61.

## Source: vNum Resource

The first 10 bytes of the INIT buffer come from a `vNum` resource (type 'vNum',
ID 0) baked into the application binary. For AOL 2.7:

```
vNum ID 0 (10 bytes): 0C B6 03 00 00 00 00 00 0C 04

  [0-1] 0C B6   Client version token -- becomes the P3 INIT token
                 0x0C = Mac platform family
                 0xB6 = AOL 2.7 build identifier
                 (AOL 3.0 Mac ships vNum 0C 03 ... instead)
  [2]   03      Version major
  [3]   00      Version minor
  [4]   00      Version patch
  [5]   00      Version build
  [6-7] 00 00   Placeholder -- overwritten at runtime with connection type
  [8-9] 0C 04   Client revision code
```

This resource is loaded at CODE 5 offset 0x56F0 (see "vNum Loading" below)
and copied to globals at A5-0x2710 through A5-0x2706.

## Source: vers Resource

```
vers ID 1 (78 bytes):
  [0]   02      Major version (BCD) = 2
  [1]   70      Minor version (BCD) = 7.0
  [2]   80      Stage = release
  [3]   00      Pre-release revision 0
  [4-5] 00 00   Region = USA
  Short string: "2.7"
  Long string:  "2.7 Copyright (c) 1987-1996 America Online, Inc."
```

The version word (bytes 0-1 = 0x0270) is stored at A5-0x377C during
initialization and copied to INIT buf[38-39].

---

## INIT Packet Builder (CODE 5, offset 0x3720)

This function constructs the 50-byte INIT packet buffer, then hands it to
the P3 layer for framing and transmission. The P3 layer wraps it with a
sync byte (0x5A), CRC, length, sequence numbers, and type byte (0xA3),
producing the final wire frame.

### Function Prologue

```asm
3720: link.w   a6, #$ffb4          ; Allocate 76 bytes of local stack space
                                    ; (0x4C = 76, stored as signed -76 = $FFB4)
3724: movem.l  d3-d7/a3-a4, -(a7)  ; Save registers we'll use
3728: movea.l  $8(a6), a3          ; A3 = first parameter (output buffer pointer)
372C: lea.l    -$40(a6), a4        ; A4 = local array at FP-64 (the sentinel array)
```

### Initialize Sentinel Array (Language Codes)

Four 16-bit words initialized to 0xFFFF ("no data"). These will hold language
codes if the client has locale information available. 0xFFFF means "unset."

```asm
3730: move.w   #$ffff, $6(a4)      ; sentinel[3] = 0xFFFF
3736: move.w   #$ffff, $4(a4)      ; sentinel[2] = 0xFFFF
373C: move.w   #$ffff, $2(a4)      ; sentinel[1] = 0xFFFF
3742: move.w   #$ffff, (a4)        ; sentinel[0] = 0xFFFF
```

### Clear Working Variables

```asm
3746: clr.w    d6                   ; D6 = 0 (will hold a capability flag)
3748: clr.l    -$4c(a6)            ; Clear local_0x4C (32-bit)
374C: clr.w    d4                   ; D4 = 0 (will hold modem/connection flag)
374E: clr.w    d5                   ; D5 = 0 (will hold processor type)
3750: clr.w    d5                   ; (redundant -- possibly compiler artifact)
3752: clr.w    -$48(a6)            ; Clear local_0x48 (session param, 16-bit)
3756: moveq    #$0, d0
3758: move.l   d0, -$46(a6)        ; Clear local_0x46 (session param, 32-bit)
375C: move.w   #$4, -$42(a6)       ; local_0x42 = 4 (max language codes)
3762: clr.b    -$33(a6)            ; Clear local_0x33 (boolean flag)
```

### Gather System Information

```asm
3766: jsr      $4f86(pc)            ; Call helper to query system capabilities
                                    ; (relative call within CODE 5)

; Check global flag at A5[-0x4008] -- appears to be an AppleTalk/networking flag
376A: tst.b    -$4008(a5)
376E: beq.b    $3774                ; If zero, D6 stays 0
3770: moveq    #$1, d0              ; Else D6 = 1
3772: bra.b    $3776
3774: moveq    #$0, d0
3776: ext.w    d0
3778: move.w   d0, d6               ; D6 = network capability flag

; D3 = 1 only if BOTH D6 and another flag at A5[-0x4011] are set
377A: moveq    #$0, d3
377C: tst.w    d6
377E: beq.b    $3788
3780: tst.b    -$4011(a5)
3784: beq.b    $3788
3786: moveq    #$1, d3
3788: tst.b    d3
378A: beq.b    $3790
378C: moveq    #$1, d0
378E: bra.b    $3792
3790: moveq    #$0, d0
3792: ext.w    d0
3794: move.w   d0, -$4c(a6)         ; local_0x4C = combined flag (bit 1 of capability byte)
```

### Query Connection Parameters

```asm
; Call JSR $12AA(A5) -- checks modem/connection state
3798: subq.l   #$2, a7              ; Reserve 2 bytes for boolean return
379A: jsr      $12aa(a5)            ; Query: is connection active/valid?
379E: tst.b    (a7)+
37A0: beq.b    $37a6
37A2: moveq    #$1, d0
37A4: bra.b    $37a8
37A6: moveq    #$0, d0
37A8: ext.w    d0
37AA: move.w   d0, d4               ; D4 = connection valid flag (bit 4 of capability byte)

; Call JSR $1BCA(A5) with selector 0x0150 -- reads a 32-bit session parameter
37AC: subq.l   #$2, a7
37AE: move.w   #$150, -(a7)         ; Selector 0x0150
37B2: pea.l    -$46(a6)             ; Output: 32-bit value -> local_0x46
37B6: moveq    #$0, d0
37B8: move.w   d0, -(a7)            ; Offset 0
37BA: moveq    #$4, d1
37BC: move.w   d1, -(a7)            ; Size = 4 bytes
37BE: jsr      $1bca(a5)            ; Read parameter

; Call JSR $1BCA(A5) with selector 0x0151 -- reads a 16-bit session parameter
37C2: subq.l   #$2, a7
37C4: move.w   #$151, -(a7)         ; Selector 0x0151
37C8: pea.l    -$48(a6)             ; Output: 16-bit value -> local_0x48
37CC: moveq    #$0, d0
37CE: move.w   d0, -(a7)
37D0: moveq    #$2, d1
37D2: move.w   d1, -(a7)            ; Size = 2 bytes
37D4: jsr      $1bca(a5)
```

### Query Processor Type via Gestalt

```asm
; Only call Gestalt('proc') if A5[-0x3CC8] is nonzero (System 7+ check)
37D8: tst.b    -$3cc8(a5)
37DC: addq.w   #$4, a7              ; Clean up stack from previous calls
37DE: beq.b    $3800                ; Skip if pre-System 7

; _Gestalt('proc')
37E0: subq.l   #$2, a7              ; Reserve space for OSErr result
37E2: move.l   #$70726f63, -(a7)    ; Push selector 'proc' (ASCII: p r o c)
37E8: pea.l    -$38(a6)             ; Push address for 32-bit Gestalt result
37EC: jsr      $30a(a5)             ; Call _Gestalt via jump table
37F0: move.w   (a7)+, d7            ; Pop error code
37F2: bne.b    $3800                ; If error, skip (leave D5 = 0)

; Gestalt('proc') returns: 1=68000, 2=68010, 3=68020, 4=68040, 5=68040
37F4: move.w   -$36(a6), d0         ; Low 16 bits of Gestalt result
37F8: ext.l    d0                    ; Sign-extend to 32 bits
37FA: move.l   d0, d5               ; D5 = raw processor type
37FC: moveq    #$20, d0             ; 0x20 = 32
37FE: add.l    d0, d5               ; D5 += 32 (offset to avoid collision with other enums)
                                    ;
                                    ; For 68040: D5 = 4 + 32 = 36 = 0x24
                                    ; This matches captured byte: 0x24
```

### Try to Fill Language Codes

```asm
; Call JSR $12A2(A5) -- attempts to fill the sentinel array with locale data
3800: subq.l   #$2, a7
3802: move.l   a4, -(a7)            ; Push sentinel array (4 x 16-bit words)
3804: pea.l    -$42(a6)             ; Push max count (4)
3808: pea.l    -$33(a6)             ; Push output flag byte
380C: jsr      $12a2(a5)            ; Try to get locale/language codes
3810: tst.b    (a7)+                ; Did it succeed?
3812: beq.b    $381a                ; If not, skip
3814: move.w   #$1, -$4a(a6)        ; local_0x4A = 1 (has locale data)
                                    ;
                                    ; If locale data unavailable, the sentinel array
                                    ; keeps its 0xFFFF values ("unset")
```

### Zero the 50-Byte Packet Buffer

```asm
381A: moveq    #$32, d0             ; 0x32 = 50 bytes
381C: move.l   d0, -(a7)            ; Push count
381E: moveq    #$0, d1
3820: move.l   d1, -(a7)            ; Push fill value (0)
3822: pea.l    -$32(a6)             ; Push buffer address (A6 - 50)
3826: jsr      $9d2(a5)             ; Call memset(buf, 0, 50)
                                    ;
                                    ; Buffer occupies A6-0x32 through A6-0x01 (50 bytes)
                                    ; buf[N] lives at A6 - (50 - N) = A6 - (0x32 - N)
```

### Fill Bytes 0-9: vNum Resource Data

The vNum resource was loaded earlier (see "vNum Loading" section below) into
globals at A5-0x2710 through A5-0x2706. The code copies 6 bytes, skips 2
(overwritten with connection type), then copies the last 2.

```asm
; Copy vNum[0:6] -> buf[0:6]
382A: move.b   -$2710(a5), -$32(a6)  ; buf[0] = vNum[0] = 0x0C (tokenHi)
3830: move.b   -$270f(a5), -$31(a6)  ; buf[1] = vNum[1] = 0xB6 (tokenLo)
3836: move.b   -$270e(a5), -$30(a6)  ; buf[2] = vNum[2] = 0x03 (versionMajor)
383C: move.b   -$270d(a5), -$2f(a6)  ; buf[3] = vNum[3] = 0x00 (versionMinor)
3842: move.b   -$270c(a5), -$2e(a6)  ; buf[4] = vNum[4] = 0x00 (versionPatch)
3848: move.b   -$270b(a5), -$2d(a6)  ; buf[5] = vNum[5] = 0x00 (versionBuild)

; Write connection type over vNum[6:8] slot
384E: move.w   -$4020(a5), -$2c(a6)  ; buf[6-7] = connection method
                                      ; (0x0009 = TCP; modem values differ)

; Copy vNum[8:10] -> buf[8:10]
3854: move.b   -$2708(a5), -$2a(a6)  ; buf[8] = vNum[8] = 0x0C (revisionHi)
385A: move.b   -$2707(a5), -$29(a6)  ; buf[9] = vNum[9] = 0x04 (revisionLo)
```

### Fill Bytes 10-15: Session Parameters

```asm
3860: move.w   -$48(a6), -$28(a6)    ; buf[10-11] = session param (16-bit, from selector 0x0151)
3866: move.l   -$46(a6), -$26(a6)    ; buf[12-15] = session param (32-bit, from selector 0x0150)
                                      ; Both are 0x0000 at INIT time (no session yet)
```

### Fill Bytes 16-17: Mac System Version (Gestalt 'sysv')

```asm
386C: move.w   -$4022(a5), -$22(a6)  ; buf[16-17] = Gestalt('sysv') result (16-bit BCD)
                                      ;
                                      ; System 7.6.1 -> 0x0761
                                      ; System 7.5.5 -> 0x0755
                                      ; System 8.1   -> 0x0810
                                      ;
                                      ; Stored by InitUnit (CODE 2) at startup via:
                                      ;   Gestalt('sysv', &result)
                                      ;   MOVE.W result, -$4022(A5)
```

### Fill Byte 18: Capability Flags (Bitfield)

A single byte encoding five boolean capabilities, each from a different
check performed earlier in the function:

```asm
; Start with whatever's in buf[18] (0 from memset), mask to 5 bits
3872: andi.b   #$1f, -$20(a6)        ; buf[18] &= 0x1F (clear upper 3 bits)

; Bit 4: connection valid (D4 from JSR $12AA)
3878: moveq    #$0, d0
387A: move.w   d4, d0
387C: andi.b   #$ef, -$20(a6)        ; Clear bit 4
3882: lsl.b    #$4, d0               ; Shift D4 into bit 4 position
3884: andi.b   #$10, d0              ; Isolate bit 4
3888: or.b     d0, -$20(a6)          ; buf[18] |= (D4 << 4)

; Bit 3: locale data available (from local_0x33)
388C: tst.b    -$33(a6)
3890: lea.l    $c(a7), a7            ; Clean stack (12 bytes from earlier pushes)
3894: beq.b    $389c
3896: bset.b   #$3, -$20(a6)         ; buf[18] |= 0x08 if locale available

; Bit 2: has locale data (local_0x4A from JSR $12A2)
389C: moveq    #$0, d0
389E: move.w   -$4a(a6), d0
38A2: andi.b   #$fb, -$20(a6)        ; Clear bit 2
38A8: lsl.b    #$2, d0
38AA: andi.b   #$4, d0
38AE: or.b     d0, -$20(a6)          ; buf[18] |= (local_0x4A << 2)

; Bit 1: combined network flag (local_0x4C)
38B2: moveq    #$0, d0
38B4: move.w   -$4c(a6), d0
38B8: andi.b   #$fd, -$20(a6)        ; Clear bit 1
38BE: lsl.b    #$1, d0
38C0: andi.b   #$2, d0
38C4: or.b     d0, -$20(a6)          ; buf[18] |= (local_0x4C << 1)

; Bit 0: network/AppleTalk capability (D6)
38C8: moveq    #$0, d0
38CA: move.w   d6, d0
38CC: andi.b   #$fe, -$20(a6)        ; Clear bit 0
38D2: andi.b   #$1, d0
38D6: or.b     d0, -$20(a6)          ; buf[18] |= (D6 & 1)
```

Capability flags byte layout:
```
  Bit 7-5: unused (always 0)
  Bit 4:   32-bit clean (client runs in 32-bit addressing mode)
  Bit 3:   extended mode (locale/language data available)
  Bit 2:   session key support
  Bit 1:   TCP available (Communications Toolbox TCP path active)
  Bit 0:   CTB present (Communications Toolbox installed)
```

Captured value: 0x10 = bit 4 set = 32-bit clean, no CTB/TCP/locale flags.

### Fill Bytes 19-25: Reserved and Processor Type

```asm
38DA: andi.b   #$0, -$1f(a6)         ; buf[19] = 0 (AND with 0 = always clear)
38E0: clr.b    -$1e(a6)              ; buf[20] = 0
38E4: move.b   d5, -$1d(a6)          ; buf[21] = processor type + 32
                                      ;
                                      ; D5 was set at 0x37FA-0x37FE:
                                      ;   Gestalt('proc') returns 4 for 68040
                                      ;   Code adds 32 -> D5 = 36 = 0x24
                                      ;
                                      ; Known values:
                                      ;   0x21 = 68000 (1+32)
                                      ;   0x22 = 68010 (2+32)
                                      ;   0x23 = 68020 (3+32)
                                      ;   0x24 = 68030 (4+32)  [note: Gestalt 4 = 68030 on most systems]
                                      ;   0x25 = 68040 (5+32)
                                      ;   0x00 = unknown (Gestalt failed, D5 stayed 0)

38E8: moveq    #$0, d0
38EA: move.l   d0, -$1c(a6)          ; buf[22-25] = 0x00000000 (reserved)
```

### Fill Bytes 26-37: Reserved (Untouched Zeros)

Bytes 26-37 are never written after the initial memset. They remain zero.
These may be reserved for future use or platform-specific data that the
Mac client doesn't populate.

### Fill Bytes 38-47: Version Word and Language Codes

```asm
38EE: move.w   -$377c(a5), -$c(a6)   ; buf[38-39] = vers resource region/country code
                                      ; (vers resource bytes 4-5, NOT the version word)
                                      ; 0x0000 = USA, 0x0001 = France, etc.
                                      ; Captured: 0x0000 = USA (correct)

; Copy the four sentinel/language words from A4
38F4: move.w   (a4), -$a(a6)         ; buf[40-41] = language[0] (0xFFFF if unset)
38F8: move.w   $2(a4), -$8(a6)       ; buf[42-43] = language[1]
38FE: move.w   $4(a4), -$6(a6)       ; buf[44-45] = language[2]
3904: move.w   $6(a4), -$4(a6)       ; buf[46-47] = language[3]
```

### Fill Byte 48: Platform ID

```asm
390A: move.b   -$2677(a5), -$2(a6)   ; buf[48] = platform byte from global
                                      ; 1 = Windows, 2 = Macintosh, 3 = DOS
                                      ; For AOL 2.7 Mac: always 0x02
```

### Send the Packet

```asm
; BlockMoveData(buf, outputParam, 50) -- copy buffer to caller's output area
3910: lea.l    -$32(a6), a0          ; A0 = source (our 50-byte buffer)
3914: movea.l  a3, a1                ; A1 = destination (parameter passed in A3)
3916: moveq    #$32, d0              ; 50 bytes
3918: dc.w     $a02e                 ; _BlockMoveData trap

; Call P3 send function with selector 0x011E
391A: subq.l   #$2, a7
391C: move.w   #$11e, -(a7)          ; P3 transmit selector
                                      ; The P3 layer wraps this 50-byte buffer
                                      ; with the frame header and transmits it
```

---

## vNum Resource Loading (CODE 5, offset 0x56F0)

This function loads the 10-byte `vNum` resource into application globals,
making it available for the INIT builder above.

```asm
56F0: link.w   a6, #$fff2            ; 14 bytes local space
56F4: move.l   a4, -(a7)             ; Save A4
56F6: clr.b    $8(a6)                ; Clear output flag
56FA: moveq    #$0, d0
56FC: move.l   d0, -$2714(a5)        ; Clear the 4-byte guard before vNum globals

; _GetResource('vNum', 0) -- load the version number resource
5700: clr.l    -(a7)                  ; Push NULL (for result)
5702: move.l   #$764e756d, -(a7)     ; Push resource type 'vNum' (0x764E756D)
5708: clr.w    -(a7)                  ; Push resource ID 0
570A: dc.w     $a9a0                  ; _GetResource trap
570C: movea.l  (a7)+, a4             ; A4 = resource handle
570E: move.l   a4, d0
5710: beq.b    $573a                  ; If NULL (not found), skip

; Copy 10 bytes from resource data to globals at A5[-0x2710]
5712: move.l   (a4), -(a7)           ; Push *handle (dereference to get data pointer)
5714: pea.l    -$2710(a5)            ; Push destination: A5-0x2710
5718: moveq    #$a, d0               ; 10 bytes
571A: move.l   d0, -(a7)
571C: jsr      $ba(a5)               ; Call BlockMoveData(rsrcData, &globals, 10)

; Release the resource handle
5720: move.l   a4, -(a7)
5722: dc.w     $a9a3                  ; _ReleaseResource trap

; Clear related globals
5724: moveq    #$0, d0
5726: move.l   d0, -$3caa(a5)
572A: moveq    #$0, d0
572C: move.l   d0, -$3ca6(a5)
```

After this function runs, globals A5[-0x2710] through A5[-0x2706] contain
the 10 bytes of the vNum resource, ready for the INIT builder to read.

---

## Complete INIT Packet Field Map

Verified against captured frame `5A C8 A5 00 34 7F 7F A3 0C B6 03 00 ...`

### P3 Frame Header (added by P3 layer, not part of the 50-byte buffer)

| Frame Byte | Value | Field |
|------------|-------|-------|
| 0 | 5A | Sync byte ('Z') |
| 1-2 | C8 A5 | CRC-16 |
| 3-4 | 00 34 | Payload length (52 = 50 buffer + 2 overhead) |
| 5 | 7F | TX sequence |
| 6 | 7F | RX sequence |
| 7 | A3 | Packet type (INIT) |

### 50-Byte INIT Buffer (frame bytes 8-57)

| buf | frame | captured | source | field |
|-----|-------|----------|--------|-------|
| 0 | 8 | 0C | vNum[0] | tokenHi -- Mac platform family |
| 1 | 9 | B6 | vNum[1] | tokenLo -- client build (B6=2.7, 03=3.0) |
| 2 | 10 | 03 | vNum[2] | versionMajor |
| 3 | 11 | 00 | vNum[3] | versionMinor |
| 4 | 12 | 00 | vNum[4] | versionPatch |
| 5 | 13 | 00 | vNum[5] | versionBuild |
| 6-7 | 14-15 | 00 09 | A5[-0x4020] | connectionType (9=TCP, others=modem) |
| 8 | 16 | 0C | vNum[8] | revisionHi |
| 9 | 17 | 04 | vNum[9] | revisionLo |
| 10-11 | 18-19 | 00 00 | selector 0x0151 | sessionParam16 (0 at INIT time) |
| 12-15 | 20-23 | 00000000 | selector 0x0150 | sessionParam32 (0 at INIT time) |
| 16-17 | 24-25 | 07 61 | Gestalt('sysv') | macSystemVersion -- BCD (0x0761=7.6.1) |
| 18 | 26 | 10 | bitfield | capabilityFlags (see bit layout above) |
| 19 | 27 | 00 | hardcoded 0 | reserved |
| 20 | 28 | 00 | hardcoded 0 | reserved |
| 21 | 29 | 24 | Gestalt('proc')+32 | processorType (0x24=68030, 0x25=68040) |
| 22-25 | 30-33 | 00000000 | hardcoded 0 | reserved |
| 26-37 | 34-45 | (zeros) | memset | reserved |
| 38-39 | 46-47 | 00 00 | A5[-0x377C] | regionCode -- vers resource country code (0=USA) |
| 40-41 | 48-49 | FF FF | sentinel array | languageCode[0] (0xFFFF=unset) |
| 42-43 | 50-51 | FF FF | sentinel array | languageCode[1] |
| 44-45 | 52-53 | FF FF | sentinel array | languageCode[2] |
| 46-47 | 54-55 | FF FF | sentinel array | languageCode[3] |
| 48 | 56 | 02 | A5[-0x2677] | platformId (1=Win, 2=Mac, 3=DOS) |
| 49 | 57 | 0D | P3 layer | p3Terminator |

### Key Differences from Windows 52-Byte Layout

The current `InitPacketParser.java` assumes the Windows field order, which is
completely different:

| Issue | Windows Parser | Mac Reality |
|-------|---------------|-------------|
| PAYLOAD_OFFSET | 6 (wrong) | 10 (after token bytes) or N/A (token IS buf[0-1]) |
| platform | buf[0] (offset 0) | buf[48] (offset 48, near end) |
| version | buf[1-2] | vNum resource (buf[0-9]) |
| systemVersion | buf[0x10] as "dosVersion" | buf[16-17] as Gestalt('sysv') BCD |
| processorType | buf[0x15] | buf[21] (Gestalt('proc') + 32) |
| memory | buf[4-5] | not in Mac INIT (use Gestalt 'ram' separately) |
| resolution | buf[0x1F-0x22] | not in Mac INIT |
| language | buf[0x28-0x2F] | buf[40-47] (sentinel 0xFFFF if unavailable) |

The parser cannot share field offsets between platforms. Mac INIT packets
need their own parsing path.
