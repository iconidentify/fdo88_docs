# AOL4Free 2.6 v4 - Deep Analysis

**Source**: `AOL4Free2.6v4.sit` (StuffIt archive, MacBinary)
**Author**: Happy Hardcore
**Date**: ~September 1995
**Platform**: Macintosh AOL 2.6

## Overview

AOL4Free is **not an FDO88 tool** -- it contains no DB resources or FDO88 binary streams. It is a **binary patcher** that modifies the AOL 2.6 client application and three Online Tools (Chat, File Transfer, Mail) to bypass AOL's billing system by exploiting the client/host trust model.

## Archive Contents

```
AOL4Free2.6 v4/
  AOL4Free2.6 v4 Docs        76KB rsrc  Documentation viewer (standalone Mac app)
  Install AOL4Free2.6 v4     31KB rsrc  Patcher application
  Remove AOL4Free2.6 v4      29KB rsrc  De-patcher (restores original files)
  Mailbomb Folder/
    ReadMe!!!                  2KB       UltraBomb instructions
    UltraBomb Macro            569B      KeyQuencer macro for mail bombing
    Icon                       3KB       Custom folder icon
```

## Technical Architecture

### How It Works

AOL4Free exploits a fundamental design flaw in AOL's client/server architecture: **the client, not the host, enforces free area restrictions**.

From the docs:

> To go to the free area, you select 'Member Services', and the client sends a 'token' to the host telling it to stop billing, and telling it to send the client the information for the 'Free Area' window. The catch is that it's the client's job to close all of the other windows. It's the client's job to tell you you can't IM and read EMAIL. The host couldn't give a shit.

The patcher modifies the AOL client to:
1. Send "enter free area" tokens to stop billing
2. Skip the client-side window closing/restriction code
3. Periodically re-send free tokens during normal activity
4. Handle edge cases around IMs and email (which AOL partially protected server-side)

### Patch Resources

The installer uses a custom patching system with these resource types:

| Type | Description |
|------|-------------|
| `ZAP` | Binary patch data (22 patches in installer, 18 in remover) |
| `ZAP#` | Patch targets: "America Online v2.6", "ChatOld", "File TransferOld", "MailOld" |
| `ZAPS` | Owner/signature resource |
| `ZVER` | Version verification: "Where is America Online v2.6?", "Where is Chat?", etc. |
| `ZIS#` | Patch instruction sets (21 entries) |
| `ZIL#` | Patch index list |
| `ZERO` | Zero-fill data |
| `DREL` | Data relocation entries |

Named ZAP resources reveal the patched subsystems:
- `InitUnit` - Initialization code
- `Libs` - Library routines
- `Events` - Event handling loop
- `P3` - P3 protocol layer (the transport that carries FDO88)
- `FormModifiers` - Form/FDO display modifiers (directly manipulates FDO88 form behavior)

### FDO88 Connection

While AOL4Free contains no FDO88 data itself, the `FormModifiers` ZAP resource is particularly relevant -- it patches the AOL client's FDO88 form interpreter to prevent the "free area" forms from closing other windows. The `P3` patch modifies the P3 protocol handler to inject billing-stop tokens into the data stream.

This is direct evidence of how the P3 + FDO88 system was exploited: the tokens that control billing flow through the same P3 transport layer that carries FDO88 atom streams.

### Stealth Mechanism (v4)

Version 4 added "stealth" capability after AOL discovered they could detect AOL4Free users through Stratus server log patterns:

> AOL found a way to detect users of AOL4Free by exploiting the fact that it generates certain kinds of error messages in Stratus Logs. However, with only a few lines of additional code AOL4Free is again undetectable!

### Internal AOL Response

The docs include leaked internal AOL staff email from August-September 1995 discussing legal action:

> From: Appelman
> To: MayLiang
> "These people are idable as stealing time. I think we have enough to go forward with legal action."

> From: MayLiang
> "We then should get verification from TOS and then hand them over to the Secret Service"

## Documentation Viewer

The `AOL4Free2.6 v4 Docs` file is a standalone Macintosh application (not a text file) containing a custom document viewer with these 68k CODE resources:

| ID | Name | Description |
|----|------|-------------|
| 0 | Main | Entry point |
| 1 | UnivProcs | Universal procedure pointers (68k/PPC bridge) |
| 2 | WindowStuff | Window management |
| 3 | FileStuff | File I/O |
| 4 | PrintStuff | Printing support |

The viewer displays 13 styled TEXT resources covering:
1. What's New in v4
2. What is AOL4Free
3. Installation instructions
4. Trust/security discussion
5. Technical explanation of the exploit
6. Detection and legal risks (with leaked AOL staff email)
7. Longevity analysis ("How long will the party last?")
8. How to become a cracker (68k assembly tutorial recommendations)
9. Philosophy ("The Conscience of a Hacker" by The Mentor, 1986)
10. Contact information
11. Troubleshooting
12. Revision history (Beta 1 through v4, June-September 1995)
13. Acknowledgements

## UltraBomb Macro

A KeyQuencer macro (`MCRO` resource, 569 bytes) that automates mail sending by:
1. Patching AOL's Mail tool to not dim the "Send Now" button after sending
2. Rapidly hitting Enter to send repeated copies
3. Achieving ~1 mail per second send rate

Invoked via Cmd-Opt-Ctrl-M. An "Enable Ultrabomb" menu item in the "Hell" menu disables free token injection during bombing for slightly faster throughput (at the cost of being billed).

## FDO88 Relevance

AOL4Free demonstrates the intimate relationship between P3 transport, FDO88 forms, and AOL's billing system:

- **Billing tokens** travel over the same P3 connection as FDO88 atom streams
- **Form behavior** (window closing, field disabling) is controlled by FDO88 commands that the client interprets -- AOL4Free patches the interpreter
- **The "Free Area"** is itself an FDO88 form (a `fdo$canned` record in the local database) that triggers billing-stop tokens
- The `FormModifiers` patch directly manipulates how FDO88 forms interact with the billing state machine

This confirms the architecture described in the FDO88 Manual: the client is responsible for enforcing form-level restrictions, and the host trusts it to do so.
