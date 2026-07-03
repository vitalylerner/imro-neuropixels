# Neuropixels 1.0-NHP Probe Configuration

## Overview

This directory contains the complete electrode geometry specification for the **Neuropixels 1.0-NHP** probe using a single authoritative CSV file.

## File

- **`channelmap.csv`** - Complete 4,416-electrode geometry map with channel assignments

## Channel Map Format

```
electrode  : Global electrode number (0-4415)
channel    : Channel this electrode can connect to (0-383)
bank       : Virtual bank (0-11)
row        : Depth row (0-2207)
col        : Column (0 or 1, for left/right)
x          : X-coordinate in micrometers (0 or 103)
y          : Y-coordinate in micrometers (0, 20, 40, ..., 44140)
ref        : Whether electrode is a reference electrode (true/false)
```

## Key Specifications

| Parameter | Value |
|-----------|-------|
| **Total Electrodes** | 4,416 |
| **Recordable Channels** | 384 |
| **Virtual Banks** | 12 |
| **Channels per Bank** | 384 |
| **Row Pitch** | 20 µm |
| **Column Pitch** | 103 µm |
| **Max Depth** | 44,140 µm (44.14 mm) |
| **Probe Type** | 0 (NP1.0) |

## Electrode-to-Channel Mapping

Each electrode can connect to exactly one channel:
```
channel = electrode_id % 384
```

Example:
- Electrode 0 → Channel 0
- Electrode 191 → Channel 191
- Electrode 384 → Channel 0
- Electrode 575 → Channel 191

## Reference Electrodes

One reference electrode per bank, located at channel position 191:

| Bank | Electrode ID |
|------|--------------|
| 0    | 191          |
| 1    | 575          |
| 2    | 959          |
| 3    | 1343         |
| 4    | 1727         |
| 5    | 2111         |
| 6    | 2495         |
| 7    | 2879         |
| 8    | 3263         |
| 9    | 3647         |
| 10   | 4031         |
| 11   | 4415         |

## IMRO Format

The probe uses **imro_np1000** format for SpikeGLX configuration files.

### IMRO File Structure

**Header:**
```
(NP1000,384)
```

**Entries (one per channel):**
```
(ChannelID, Bank, Reference, APgain, LFgain, Filter)
```

### Field Definitions

| Field | Range | Description |
|-------|-------|-------------|
| **ChannelID** | 0-383 | Sequential channel identifier |
| **Bank** | 0-1 | Which electrode bank (NP1.0 has 2 banks) |
| **Reference** | 0-4 | Reference electrode: 0=external, 1=tip, 2-4=on-shank |
| **APgain** | 50-3000 | AP band amplification (typically 500) |
| **LFgain** | 50-3000 | LF band amplification (typically 250) |
| **Filter** | 0-1 | AP highpass filter: 1=ON, 0=OFF |

### Example IMRO File

```
(NP1000,384)
(0,0,1,500,250,1)
(1,0,1,500,250,1)
(2,0,1,500,250,1)
...
(383,1,1,500,250,1)
)
```

### Reference Notes

- Bank assignment determines which physical electrodes are connected to each channel
- For Neuropixels 1.0, Bank 0 and Bank 1 cover different depth regions on the same shank
- On-shank references are at electrode positions 191 (bank 0), 575 (bank 1), etc.
