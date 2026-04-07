# FDO88 Menu Operation (MOP) Codes

From Appendix E of the FDO88 Manual (January 1994, Release 1.0).
Verified against source PDF pages E-1 through E-10.

## FDO Commands Using MOP Codes

MOP codes are used in the dispatch argument of these FDO commands:
- fdo$dispch ($05)
- fdo$ImdDispatch ($C3)
- fdo$MenuItem ($C0)
- fdo$NotifDispatch ($C5)
- fdo$ResetDispch ($B2)

## Dispatch Argument Format

All dispatch-carrying commands share a 6-byte dispatch argument:

```
Byte 1:    <MOP_code>           1-byte MOP code
Byte 2-3:  <token><s_code>      2-byte encoded token + surcharge code
Byte 4:    subparm1             MOP-specific parameter
Byte 5:    subparm2             MOP-specific parameter
Byte 6:    subparm3             MOP-specific parameter
```

Surcharge codes in the token field:
- plus_same (0): Action allowed from paid or free area
- plus_pay (1): Action allowed from paid area only
- plus_free (2): Action allowed from free area only

Note: MOP code values 129-155 equal MOP code values 1-127 (high bit set
in forms received from the host).

## MOP Code Table (Table E.1)

| Num | Name | Description |
|-----|------|-------------|
| 1 | Ask_DB | Looks for window on-screen. If not on-screen and token is 'K1', checks disk copy of host library. If no record, asks host. |
| 2 | Ask_Host | Looks for window on-screen. If not on-screen, asks host for window. |
| 3 | TokenW | Sends token with no data. Turns on host respond timer. |
| 4 | Token | Sends token. Pops number of windows specified in subparm1 and subparm2. No wait state. |
| 5 | Pop | Pops the front-most form. |
| 6 | Send_DB | Sends the number of bytes from local database record specified in subparm1, subparm2, and subparm3 of MOP_info to host. |
| 7 | Echo_Send | Sends source field specified in subparm2 of MOP_info to host. |
| 8 | Ask_No_Magic | Sends request to host. Does not look for window on-screen. |
| 9 | Pop_Send | Sends form. Pops form after sending. |
| 10 | Send_Form | Sends member-entered information to the host computer. |
| 11 | Send_Selected | Sends selected fields to host. Allows specifying which fields via subparm bitmasks. |
| 12 | Save_Field | Saves the field specified in subparm1 of MOP_info (from front-most window) to disk. Prompts member for file name. |
| 13 | Load_Field | Allows member to select text file. Inserts contents into the field in the front-most window specified in subparm1 of MOP_info. |
| 15 | Mop_Local_Token | Executes the enclosed token as if it were received from the host with no data. |
| 16 | Ask_DB_Pop | Pops front-most window. Then looks for window on-screen. If not on-screen and token is 'K1', checks disk copy of host library. If no record, asks host. |
| 17 | Ask_Indirect | Sends the token from this dispatch to the host. Gets param bytes from field pointed to by subparm3 of MOP_info. |
| 18 | Xeq_Indirect | Gets and executes dispatch from field pointed to by subparm3 of MOP_info. |
| 23 | Log_Fail | Closes login progress windows and repaints signon screen if there is a login failure. |
| 36 | Private_Event | Executes private event specified in subparm1 of MOP_info. Passes subparm2 and subparm3 to private event. |
| 37 | Show_Local_Form | Finds local copy of host library form. Does not look for window on-screen or ask host for record. |
| 38 | Tool_Window_Pop | Sends toolkitDispatch event to tool that owns window. Passes subparm2 and subparm3 (the specific dispatch) of MOP_info to tool in value1. Pops form if LSB of subparm1 is set. |
| 39 | Tool_Cluster | Sends toolkitDispatch event to tool whose ID is specified in subparm2 and subparm3 of MOP_info. Passes subparm1 (the specific dispatch) to tool in value1. |
| 40 | Tool_Clust_Start | Sends srMop start/restart message to tool whose cluster is named in subparm2 and subparm3 of MOP_info. |
| 41 | Toolkit_Token | Action depends on token: HC = help for current window, HM = help for main window, PC = tool preferences main category, PS = tool preferences subcategory. |
| 42 | Tool_Window | Sends toolkitDispatch event to tool which owns window. Passes subparm2 and subparm3 (the specific dispatch) of MOP_info to tool in value1. |
| 43 | Tool_Cluster_Pop | Passes toolkitDispatch message to tool whose ID is named in subparm2 and subparm3 of MOP_info. The dispatch is specified in subparm1. The tool must be running. Pops front form before invoking tool. |
| 48 | Ask_Host_Pop | Pops front-most form. Looks for window on-screen. If not on-screen, asks host for form. |

## Key MOP Codes for Server Implementation

### MOP 23 (Log_Fail)
Closes login progress windows and repaints the sign-on screen. This is the
only documented MOP that explicitly closes the progress windows. Can be
triggered from the server via fdo$ImdDispatch:
```
C3 17 00 00 00 00 00    fdo$ImdDispatch Log_Fail
```

### MOP 15 (Mop_Local_Token)
Executes the enclosed token as if received from the host. Can be used with
fdo$ImdDispatch to simulate token receipt locally:
```
C3 0F [token] 00 00 00  fdo$ImdDispatch Mop_Local_Token
```

### MOP 36 (Private_Event)
Executes internal events. The sign-on button uses Private_Event with
subparm1=$0E to trigger the sign-on sequence:
```
fdo$dispch Private_Event $0000 $0E $00 $00
```

### Send_Form subparm1 Values (Table E.2)

| Bit | Value | Action |
|-----|-------|--------|
| 7 | 128 ($80) | Sends the three subparameters of the clicked button to the host. |
| 2 | 4 ($04) | Sends all or part of text from selected list item. subparm2 = start offset, subparm3 = char count (0=all). |
| 1 | 2 ($02) | Sends the subparameters of MOP_info from the dispatch of the currently selected item. |
| 0 | 1 ($01) | Sends a number indicating the index of the selected list item. |

### Send_Selected Fields (Table E.3)

subparm1: bits 0-7 select fields 17-24
subparm2: bits 0-7 select fields 9-16
subparm3: bits 0-7 select fields 1-8

## Detailed MOP Descriptions (from Appendix E)

### Ask_DB (MOP 1)

When Ask_DB is the MOP_code, the system attempts to display a form from
the host library. If the token is 'K1', the system checks for a local copy
of this library record. If a local copy is found, it is processed as a form.

If a local copy is not found, or the token is not 'K1', the token and the
subparameters of MOP_info are sent to the host computer. The host then
gets the library record and sends the form to the client.

Library record encoding in MOP_info:
- subparm1 = library number (database)
- subparm2 + subparm3 = 2-byte record number

Example: `fdo$dispch 129 ('K1',0) $08 $BA $19`
- MOP 129 = Ask_DB (129-128=1, high bit set for host forms)
- Token 'K1' with surcharge code 0 (any area)
- Library $08, record $BA19

### Ask_DB_Pop (MOP 16)

Same as Ask_DB (MOP 1) except the front-most window is popped after
the form is processed.

### Ask_Indirect (MOP 17)

Connects a button to an item on a list. When the member presses the
button, the dispatch looks at the token and subparm1 value. subparm1
points to another field where other subparameter values are stored.
Once the token and subparameters are established, executes Ask_DB.

Example: Button with MOP 17, token 'K1', subparm1=1
- subparm1 (value 1) points to field 1 (a list field)
- When pressed, extracts the three subparameter values from the
  currently selected list item and executes Ask_DB with them.

### Xeq_Indirect (MOP 18)

Same as Ask_Indirect (MOP 17) except it executes the entire dispatch
from the selected field (not just the subparameters).

### Send_Form (MOP 10)

Sends member-entered information to the host. By default sends contents
of all input text fields. Other field types (radio, check, popup) require
the FFSSendform boolean (boolean 4) to be set.

subparm1 determines what data to send (Table E.2):
- Bit 7 ($80): Sends the three subparameters of the clicked button
- Bit 2 ($04): Sends text from selected list item (subparm2=start offset, subparm3=char count, 0=all)
- Bit 1 ($02): Sends subparameters from dispatch of currently selected item
- Bit 0 ($01): Sends index of selected list item (field number + index)

Example: `fdo$dispch Send_Form ('S1',0) $04 $02 $00`
- Sends all text of currently selected list item starting from first character

### Send_Selected (MOP 11)

Same as Send_Form except allows specifying which fields to send via
bitmasks in subparm1/2/3:
- subparm1: bits 0-7 select fields 17-24
- subparm2: bits 0-7 select fields 9-16
- subparm3: bits 0-7 select fields 1-8

Example: `fdo$dispch Send_Selected ('S1',0) $02 $06 $01`
- subparm1=$02: sends dispatch subparams from selected list item
- subparm2=$06: bits 1+2 set = sends data from fields 10 and 11
- subparm3=$01: bit 0 set = sends data from field 1

### Log_Fail (MOP 23)

Closes login progress windows and repaints the sign-on screen if there
is a login failure. This is the only documented mechanism that explicitly
closes the login progress windows.

### Private_Event (MOP 36)

Executes a private (internal) event. subparm1 specifies the event,
subparm2 and subparm3 are passed as parameters.

Known private events:
- $0E: Sign-on sequence (from sign-on form's "Sign On" button)

### Show_Local_Form (MOP 37)

Finds local copy of host library form. Does NOT look for window on-screen
or ask host for record. Always uses the local database.

### Ask_Host_Pop (MOP 48)

Pops front-most form. Looks for window on-screen. If not on-screen, asks
host for form. Never checks local database.

## Host Library Record Numbers

The 3-byte library record in MOP_info encodes:
- Byte 1 (subparm1): Library/database number
- Bytes 2-3 (subparm2+subparm3): Record number (big-endian)

Known library numbers from canned forms:
- $00: General forms
- $02: Unknown (used in welcome screen dispatches)
- $03: Unknown
- $08: Host library (main content database)

The local Online Database maps host library records to local DB resources
(DB11-DB16) via the `main.idx` index file. When Ask_DB with token 'K1'
looks for a local copy, it uses this index to find the corresponding
DB resource.
