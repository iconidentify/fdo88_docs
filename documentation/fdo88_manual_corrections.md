# FDO88 Manual -- Missing Command Definitions

14 commands listed in Appendix D of the FDO88 Manual (January 1994) were missed
during OCR processing. This document records each command's full definition as
found (or not found) in the PDF.

Source: `aol_manual.pdf` (~234 pages, 28.4MB)
Page offset: PDF page = manual page number + 8 (approximately)

---

## 1. fdo$AnimFrame

- **Opcode:** 201 ($C9)
- **Sub-opcode:** N/A
- **Manual location:** NOT FOUND in Chapter 2

The command is listed in Appendix D (Table D.1 alphabetical and Table D.2
numerical at opcode $C9 / 201) but has no definition page in Chapter 2. The
alphabetical command listing jumps directly from the 248_Extended commands
(TypedMakeMenu at 2-25, TypedMenuItem at 2-26/27, TypedTitle at 2-29/30) to
fdo$break (2-31). No AnimFrame definition exists anywhere between them or
elsewhere in the chapter.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists in
the manual. The command likely controls animation frame display for MultiIcon
fields but was never fully documented.

---

## 2. fdo$DontUse

- **Opcode:** 248 ($F8)
- **Sub-opcode:** 13 ($0D)
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2) as fdo$DontUse with opcode $F8,
sub-opcode $0D (13). No definition page exists in Chapter 2. The alphabetical
listing goes directly from fdo$Domain (2-48) to fdo$EnableField (2-49) with
no DontUse page between them.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
The name itself strongly suggests this is a reserved/deprecated extended
opcode that was intentionally left undocumented.

---

## 3. fdo$icon

- **Opcode:** 16 ($10)
- **Sub-opcode:** N/A
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2 at opcode $10 / 16). No definition
page exists in Chapter 2. The command listing goes directly from fdo$hold
(2-70) to fdo$ImdDispatch (2-71) with no icon page between them.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
This is a low-byte opcode ($10) that likely places an icon in the legacy
Apple II/Tandy character-coordinate system, superseded by fdo$MacIcon ($B9)
and fdo$MultiIcon ($C8) for Macintosh.

---

## 4. fdo$ImageToolSetup

- **Opcode:** 248 ($F8)
- **Sub-opcode:** 15 ($0F)
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2) as fdo$ImageToolSetup with opcode
$F8, sub-opcode $0F (15). No definition page exists in Chapter 2.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
The name suggests it configures an image-rendering tool (SketchImage or
ToolImage field setup), but no documentation was written for it.

---

## 5. fdo$inpdef

- **Opcode:** 7 ($07)
- **Sub-opcode:** N/A
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2 at opcode $07 / 7). No definition
page exists in Chapter 2. The listing goes from fdo$ImdDispatch (2-71)
directly to fdo$MacIcon (2-72) with no inpdef page.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
This is a low-byte opcode that likely defines input field parameters in the
legacy Apple II/Tandy character-mode system. Compare with fdo$field ($02)
and fdo$Field16 ($A1) which serve similar roles for Macintosh pixel
coordinates.

---

## 6. fdo$MacWndo

- **Opcode:** 153 ($99)
- **Sub-opcode:** N/A
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2 at opcode $99 / 153). No definition
page exists in Chapter 2. The listing goes from fdo$MacIcon (2-72/73)
directly to fdo$MakeMenu (2-74/75) with no MacWndo page.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
The name suggests a Macintosh-specific window creation command, possibly an
alternative to fdo$Window16 ($A6) with different parameters or behavior.

---

## 7. fdo$MenuItem

- **Opcode:** 192 ($C0)
- **Sub-opcode:** N/A
- **Manual location:** PDF pages 90-91 (manual pages 2-82 to 2-83)

### Description

fdo$MenuItem adds a menu item to the menu created with fdo$MakeMenu. The menu
is identified with a cluster and menu ID. For more information, see the
fdo$MakeMenu definition.

### Syntax

```
fdo$MenuItem <menu_cluster> <menu_id> <position> <menu_item_flag>
             <key> <child_menu_id> <MOP_code> (<token><s_code>)
             <MOP_info> <title>
```

| Parameter | Description |
|-----------|-------------|
| `<menu_cluster>` | 2-byte integer parameter that identifies the menu cluster of the menu to which the new menu item is added. Menu cluster values are listed in Table C.13 in Appendix C. |
| `<menu_id>` | 2-byte integer parameter that identifies the menu to which the new menu item is added. Values are 0 to 5000. |
| `<position>` | 1-byte integer parameter that designates the item's position within the menu. Values are 0 to 255. |
| `<menu_item_flag>` | 1-byte integer parameter that specifies when the menu item is enabled. Menu item flag values are listed in Table C.8 in Appendix C. |
| `<key>` | 1-byte ASCII equivalent of the keyboard character which, when pressed, selects the menu item. |
| `<child_menu_id>` | 1-byte menu ID of the next item to be displayed when this menu item is selected. |
| `<MOP_code> (<token><s_code>) <MOP_info>` | Standard dispatch argument that is a combination of a menu operation code (MOP), token, and a special 6-byte surcharge code. For more information on this dispatch argument, see the fdo$dispch definition. |
| `<title>` | Variable-length string parameter that designates the menu item title. This is a zero-terminated text argument (i.e., a text string with a 0 appended to it to signify its end). |

### Example

```
fdo$MakeMenu $1025 0050 0000 0000 0000 03 $00 "Mail"
fdo$MenuItem $1025 0050 255 00 $4D 00 $2F $0000 $00 $04 $D3 "Compose Mail"
```

This example adds a single entry to a newly created menu.

The first command creates a new menu titled Mail positioned to the immediate
left of the Windows menu. See the fdo$MakeMenu definition.

The second command adds a single entry to the new menu:

| Value | Meaning |
|-------|---------|
| $1025 | Sets the cluster and ID for the menu item to the Mail cluster. |
| 0050 | Sets the menu ID to 50. |
| 255 | Places the new item at the end of the existing menu commands. |
| 00 | Specifies that this menu item is always enabled. |
| $4D | Sets the command key associated with this item to "M." |
| 00 | Specifies that this item does not have an attached sub-menu. |
| $2F $0000 $00 $04 $D3 | Assigns a dispatch to this menu item. When this item is selected from the Mail menu, the local database is asked to display the form identified by the last three bytes of the dispatch ($00, $04, $D3). |
| "Compose Mail" | Sets the name of this menu item to "Compose Mail." |

### Platforms

Macintosh

---

## 8. fdo$ResizeRules

- **Opcode:** 248 ($F8)
- **Sub-opcode:** 6 ($06)
- **Manual location:** PDF pages 111-112 (manual pages 2-103 to 2-104)
- **Note:** Listed as "fdo$ResizeRules" in Appendix D but documented in Chapter 2 as "fdo$ResizeRule" (without trailing 's')

### Description

fdo$ResizeRule sets the rules used for resizing the individual fields within a
window when the member resizes that window. Specify rules for resizing in
either the X (horizontal) or Y (vertical) dimension.

Note: To use the fdo$ResizeRule command with the form_edit tool, you must enter
the fdo$248_Extended $06 form of the command in your code.

### Syntax

```
fdo$ResizeRule <field_no> <FieldRuleX> <FieldRuleY>
```

| Parameter | Description |
|-----------|-------------|
| `<field_no>` | 1-byte integer parameter that is the number of the field where resize rules are to be changed. |
| `<FieldRuleX>` | 1-byte integer parameter that specifies the new resizing rule to be used for sizing and positioning the target field in the X (horizontal) direction. Values: 0 = default rule, 1 = anchor to left (or top), 2 = anchor to right (or bottom), 3 = grow to take up all extra space (default for major field), 4 = maintain distance from center, 5 = keep relative position within window, 6 = keep position relative to major field, 7 = same as 5 plus resize in proportion to window change, 8 = same as 6 plus resize in proportion to major field change. |
| `<FieldRuleY>` | 1-byte integer parameter that specifies the new resizing rule for the Y (vertical) direction. Values are the same as for FieldRuleX. |

### Example

```
fdo$Field16 Button 195 0100 100 0020 $00
fdo$text 00 4
fdo$ResizeRule 00 $04 $00
```

This example creates a button in field 00 with a FieldRuleX value of 4, which
causes the field to maintain the same distance from the center of the window.

The 00 value for the field_no parameter of the fdo$text command indicates that
the current field is affected. The current field is the field that was just
defined using the fdo$field or fdo$field16 command in the FDO data stream.

### Platforms

Macintosh

---

## 9. fdo$SetData

- **Opcode:** 210 ($D2)
- **Sub-opcode:** N/A
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2 at opcode $D2 / 210). No definition
page exists in Chapter 2. The listing goes from fdo$SetCheck (2-109) directly
to fdo$SetClosePriority (2-110/111) with no SetData page between them.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
The opcode falls between SetValue ($D1/209) and SetCheck ($D5/213) in the
numerical table. The name suggests it sets arbitrary data on a field, possibly
similar to fdo$TypedData but with different semantics.

---

## 10. fdo$ToolFScrollMax

- **Opcode:** 248 ($F8)
- **Sub-opcode:** 12 ($0C)
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2) as fdo$ToolFScrollMax with opcode
$F8, sub-opcode $0C (12). No definition page exists in Chapter 2. The listing
goes from fdo$ToolQEvent (2-140) directly to fdo$TypedData (2-141) with no
ToolFScrollMax or ToolFScrollVal pages.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
The name suggests it sets the maximum scroll value for a tool-owned field's
scroll bar.

---

## 11. fdo$ToolFScrollVal

- **Opcode:** 248 ($F8)
- **Sub-opcode:** 14 ($0E)
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2) as fdo$ToolFScrollVal with opcode
$F8, sub-opcode $0E (14). No definition page exists in Chapter 2 (same gap
as ToolFScrollMax above).

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
The name suggests it sets the current scroll position value for a tool-owned
field's scroll bar.

---

## 12. fdo$TypedMenuItem

- **Opcode:** 248 ($F8)
- **Sub-opcode:** 32 ($20)
- **Manual location:** PDF pages 155-157 (manual pages 2-147 to 2-149)
- **Also appears as:** fdo$248_Extended (TypedMenuItem) at PDF pages 34-36 (manual pages 2-26 to 2-28)

### Description

fdo$TypedMenuItem is used in place of fdo$MenuItem when typed data is sent
rather than 7-bit ASCII text. fdo$TypedMenuItem adds a menu item to the menu
created with fdo$TypedMakeMenu. Only ASCII, Unicode, and compressed Unicode
types are meaningful to this command.

Note: To use the Fdo$TypedMenuItem command with the form_edit tool, you must
enter the fdo$248_Extended $20 form of the command in your code.

The text sent by fdo$TypedMenuItem can be in any defined language or script,
but the Macintosh is restricted to using the system script chosen by the
member. For example, if the text is sent in Hebrew and the member has chosen
English as the Macintosh system script, the text appears in the English
equivalents of the keys used to type the Hebrew text.

### Syntax

```
fdo$TypedMenuItem <menu_cluster> <menu_id> <position> <menu_item_flag>
                  <key> <child_menu_id> <MOP_code> (<token><s_code>)
                  <MOP_info> <title> <type> <data>
```

| Parameter | Description |
|-----------|-------------|
| `<menu_cluster>` | 2-byte parameter that identifies a particular group of windows or menus. This parameter specifies the cluster of the menu to which the new menu item is added. Table C.13 in Appendix C lists the current menu_cluster names and describes the types of windows or menus they represent. |
| `<menu_id>` | 2-byte integer parameter used to associate a specific menu to the menu item being added. Each menu in an FDO stream must be assigned a unique number. Values are 0 to 5000. |
| `<position>` | 1-byte integer parameter that defines the item's position within the menu. |
| `<menu_item_flag>` | 1-byte integer parameter that specifies when the menu item is to be enabled. See Table C.8 in Appendix C for menu_item_flag values. |
| `<key>` | 1-byte parameter that defines the ASCII equivalent of the keyboard character which, when pressed, selects the menu item. |
| `<child_menu_id>` | 1-byte parameter that designates the menu ID of the next item to be displayed when this menu item is selected. |
| `<MOP_code> (<token><s_code>) <MOP_info>` | Standard dispatch argument that is a combination of a menu operation code (MOP), token, and a special 6-byte surcharge code. For more information on this dispatch argument see the fdo$dispch definition. |
| `<title>` | Variable-length string parameter that designates the menu item title. This is a zero-terminated text argument (a text string with a 0 appended to it to signify its end). |
| `<type>` | 2-byte integer parameter that identifies the type. Values: $0000 = ASCII, $1000-$13FF = Unicode, $1400-$17FF = Compressed Unicode. |
| `<data>` | Byte stream containing the data for the menu item. The end of the stream is determined from the length of the FDO command. |

### Example

```
fdo$TypedMakeMenu $1025 0050 0000 0000 0000 03 $00 $0000 $4D $61 $69 $6C
fdo$TypedMenuItem $1025 0050 255 00 $4D 00 $2F $0000 $00 $04 $D3 $0000
                  $43 $6F $6D $70 $6F $73 $65
```

In this example, the fdo$TypedMenuItem command adds a single entry to the new
menu created by the fdo$TypedMakeMenu command. The parameter values:

| Value | Meaning |
|-------|---------|
| $1025 | Sets the cluster to the mail cluster. |
| 0050 | Sets the ID for the menu item to 50. |
| 255 | Places the new item at the end of the existing menu commands. |
| 00 | Specifies that this menu item is always enabled. |
| $4D | Sets the associated command key to "M." |
| 00 | Specifies that this item does not have an attached sub-menu. |
| $2F $0000 $00 $04 $D3 | Specifies the action code or dispatch to be assigned to this menu item. When this item is selected from the Mail menu, the local database is asked to display the form identified by the last three bytes of the dispatch ($00, $04, $D3). |
| $0000 | Sets the type of the name of this menu item to ASCII. |
| $43 $6F $6D $70 $6F $73 $65 | Sets the name of this menu item to the string "Compose Mail." |

### Platforms

Macintosh

---

## 13. fdo$UseMacRec

- **Opcode:** 162 ($A2)
- **Sub-opcode:** N/A
- **Manual location:** NOT FOUND in Chapter 2

Listed in Appendix D (Table D.1 and D.2 at opcode $A2 / 162). No definition
page exists in Chapter 2. The listing goes from fdo$UseDisplay (2-152)
directly to fdo$UseRelativeRect (2-153/154) with no UseMacRec page.

**Status:** Listed in Appendix D only. No Chapter 2 definition page exists.
The name suggests it switches to using Macintosh rectangle coordinates (Rect
structure: top, left, bottom, right) for subsequent field positioning, as
opposed to the character-coordinate system used by the legacy platforms.

---

## 14. fdo$FontSizeStyleColor

- **Opcode:** Unknown
- **Sub-opcode:** Unknown
- **Manual location:** NOT FOUND anywhere in the PDF

This command does NOT appear in Appendix D (neither Table D.1 alphabetical
nor Table D.2 numerical). It is not documented in Chapter 2. No reference to
"FontSizeStyleColor" exists anywhere in the FDO88 Manual.

**Status:** Not in the manual at all. This command may come from a later
revision of the FDO protocol (post-January 1994), or it may be a name used
only in the AOL client binary/source code that was never added to the
engineering manual. The closest documented command is fdo$TextDesc ($A8/168),
which sets font number, font size, style flag, and color as four 1-byte
parameters for the next fdo$field in the stream.

---

## Summary Table

| # | Command | Opcode | Sub-opcode | Found in PDF? | Page |
|---|---------|--------|------------|---------------|------|
| 1 | fdo$AnimFrame | $C9 (201) | -- | Appendix D only | N/A |
| 2 | fdo$DontUse | $F8 (248) | $0D (13) | Appendix D only | N/A |
| 3 | fdo$icon | $10 (16) | -- | Appendix D only | N/A |
| 4 | fdo$ImageToolSetup | $F8 (248) | $0F (15) | Appendix D only | N/A |
| 5 | fdo$inpdef | $07 (7) | -- | Appendix D only | N/A |
| 6 | fdo$MacWndo | $99 (153) | -- | Appendix D only | N/A |
| 7 | fdo$MenuItem | $C0 (192) | -- | YES | 2-82/83 |
| 8 | fdo$ResizeRules | $F8 (248) | $06 (6) | YES (as "ResizeRule") | 2-103/104 |
| 9 | fdo$SetData | $D2 (210) | -- | Appendix D only | N/A |
| 10 | fdo$ToolFScrollMax | $F8 (248) | $0C (12) | Appendix D only | N/A |
| 11 | fdo$ToolFScrollVal | $F8 (248) | $0E (14) | Appendix D only | N/A |
| 12 | fdo$TypedMenuItem | $F8 (248) | $20 (32) | YES | 2-147/149 |
| 13 | fdo$UseMacRec | $A2 (162) | -- | Appendix D only | N/A |
| 14 | fdo$FontSizeStyleColor | unknown | unknown | NOT IN MANUAL | N/A |

**Result:** Of the 14 commands, only 3 have full Chapter 2 definitions that were
missed by OCR (MenuItem, ResizeRules/ResizeRule, TypedMenuItem). The remaining
10 are listed in Appendix D's reference tables but were never given definition
pages in Chapter 2. FontSizeStyleColor does not appear anywhere in the manual.
