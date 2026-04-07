# AT Token Family Wire Format

## Token Case Encoding (from 3.0 atomizer.c)

| Token | Hex | Stream ID Size |
|-------|-----|---------------|
| AT | 0x4154 | 2 bytes |
| At | 0x4174 | 3 bytes |
| at | 0x6174 | 4 bytes |
| aT | 0x6154 | 0 bytes (generated internally) |

## AT Frame Format
```
P3 DATA frame:
  [5A] [CRC:2] [LEN:2] [TX] [RX] [0x20] [41 54] [SID:2] [data...] [0D]
```

## aT Frame (Housekeeping)
The aT frame in the 3.0 post-Dd flow carries atom control data:
```
Payload: 20 01 01 12 00
  20 01 = UNI_START_STREAM (protocol 0, atom 1)
  01 12 00 = protocol 1 (DISPLAY), atom 18 (UNI_WAIT_OFF_END_STREAM), length 0
```

This is the FDO91 atom encoding. The FDO88 equivalent may differ.

## Multi-Frame Delivery
FDO88 data split at fdo$break boundaries. Same stream ID across all frames.
Last frame ends with fdo$enddef (0x09), others end with fdo$break (0x16).

## Protocol Control Tokens (NO stream ID)
| Token | Purpose |
|-------|---------|
| EW (0x4557) | SetConnectionState(1) -- zero payload |
| EC (0x4543) | SetConnectionState(0) -- zero payload |
| SD (0x5344) | Sign-on data -- zero payload (processes pre-stored data) |

These tokens should NOT have stream ID bytes prepended.
