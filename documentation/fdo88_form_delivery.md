# FDO88 Form Delivery Protocol for AOL 2.7

## Form Delivery Token: AT (0x4154)

Forms are delivered via the AT token with a 2-byte stream ID prefix.
The AT token is confirmed to be processed by the 2.7 client -- FDO88
opcodes execute (sounds play, side effects occur).

### Wire Format
```
P3 DATA frame:
  [5A] [CRC:2] [LEN:2] [TX] [RX] [0x20] [41] [54] [SID:2] [FDO88...] [0D]
                                          "A"  "T"   stream   form
                                                      ID      data
```

### Multi-Frame Delivery
Split FDO88 data at fdo$break (0x16) boundaries. Each chunk is a separate
AT frame with the SAME stream ID. Last chunk ends with fdo$enddef (0x09).

### Token Family (from 3.0 atomizer.c)
| Token | Stream ID Size | Use |
|-------|---------------|-----|
| AT (0x4154) | 2 bytes | Standard form delivery |
| At (0x4174) | 3 bytes | Form delivery variant |
| at (0x6174) | 4 bytes | Form delivery variant |
| aT (0x6154) | 0 bytes | Housekeeping/control |

### NOT Form Delivery Tokens
| Token | Actual Function |
|-------|----------------|
| OT (0x4F54) | Network News alert (confirmed by 3.0 source + screenshot) |
| oT (0x6F54) | Network News text entries (confirmed by screenshot) |
| XS (0x5853) | Sign-OFF / disconnect |
| D* (0x442A) | Disconnect |

## Key FDO88 Switch for Sign-On Transition

From the official FDO88 Manual:

**fdo$Switch CloseSignOn (switch 87):**
"Closes the sign on progress screens, broadcasts a 'We are now online'
message to tools and indicates that the Welcome screen is in place.
Used immediately before an fdo$Window command."

Binary encoding: `C1 02 57 00` (fdo$Switch, 2 bytes, switch 87, param 0)

**fdo$Switch SetMailboxICON (switch 200):**
"Sets a flag indicating that the Welcome screen is completed and sets
the Welcome screen's mailbox icon to the appropriate state."

## Current Status

AT token is processed by the client but forms don't render as windows yet.
The client stays at "Opening connection." The P3 SS/SSR handshake exchange
may be required before the client's form system fully activates.

## Verified FDO88 Content

The real welcome screen form (DB16_252 from the Online Database) is 254 bytes
and decompiles correctly. Located at:
`binary_analysis/online_database_forms/DB16_252.bin`
