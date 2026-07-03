# IMRO Generator — Developer Guide (Overview)

## Purpose

`ImroGenerator` is a utility class for generating and parsing Neuropixels NP1.0 **IMRO configuration files**. IMRO files define which channels are active on a probe and their settings (bank, reference, gain, filter).

**Why?** Recording from a Neuropixels probe requires exporting a per-probe configuration file. The ImroGenerator automates this task, especially for depth-based channel selection.

## Design Overview

The `ImroGenerator` class in `GUI/imro_generator.py` provides three main functions:

1. **`generate_imro_content(channel_list)`** — Create IMRO file content from a list of channel tuples
2. **`parse_imro_file(content)`** — Read IMRO file content and extract channel configuration
3. **`create_channel_list_by_depth(...)`** — High-level: generate channel list from depth range and preferences

### Class Architecture

```
ImroGenerator (static utility class)
  ├─ Probe constants (TOTAL_CHANNELS, VIRTUAL_BANKS, CHANNELS_PER_BANK, etc.)
  ├─ IMRO file I/O
  │   ├─ generate_imro_content(channel_list) → str
  │   └─ parse_imro_file(content: str) → (num_channels, channel_list)
  ├─ Channel generation
  │   └─ create_channel_list_by_depth(...) → channel_list
  └─ Configuration extraction
      └─ extract_config_from_channels(channel_list) → dict
```

## Core Data Structures

### Channel Tuple

Each channel is represented as:

```python
(ch_id, bank, ref_id, ap_gain, lf_gain, ap_filter)
```

| Field | Range | Meaning |
|-------|-------|---------|
| `ch_id` | 0–383 | Channel number on the probe |
| `bank` | 0–11 | Virtual bank (determines electrode group and depth coverage) |
| `ref_id` | 0 or 1–11 | Reference electrode: 0 = external, 1–11 = tipbank reference |
| `ap_gain` | 500–1000 | Gain for action potential band |
| `lf_gain` | 250–1000 | Gain for local field potential band |
| `ap_filter` | 0 or 1 | High-pass filter on AP band: 0 = off, 1 = on |

### IMRO File Format

```
(0,N)(ch0_tuple)(ch1_tuple)...(chN-1_tuple)
```

Example:

```
(0,192)(0 1 0 500 250 1)(1 1 0 500 250 1)(2 1 0 500 250 1)...(191 11 0 500 250 1)
```

Header tuple: `(0, N)`
- First 0 = probe type (NP1.0)
- N = number of channels configured

## NP1.0 Probe Geometry

The NP1.0 probe has:
- **4416 total electrodes** arranged as 2 columns with alternating odd/even numbering (2208 per column)
- **20 µm vertical spacing** within each column (between contact centers)
- **103 µm horizontal spacing** between the two columns
- **44.16 mm length** (2208 contacts × 20 µm per column)
- **2 columns** of staggered contacts (even: 0, 2, 4, ...; odd: 1, 3, 5, ...)

**Depth calculation:**

Due to the 2-column alternating structure (odd/even numbering), depth depends on position within the column:

```python
column_position = electrode_id // 2  # Position within the column (0 to 2207)
electrode_depth_µm = column_position × 20  # 20 µm vertical spacing
depth_mm = electrode_depth_µm / 1000
```

**Bank-channel to electrode mapping:**

```python
electrode_id = ch_id + bank × 384
```

Example (depth calculation from electrode_id):
- Electrode 0 (left col, pos 0) → (0 // 2) × 20 µm = 0 µm
- Electrode 1 (right col, pos 0) → (1 // 2) × 20 µm = 0 µm
- Electrode 2 (left col, pos 1) → (2 // 2) × 20 µm = 20 µm
- Electrode 4414 (left col, pos 2207) → (4414 // 2) × 20 µm = 44,140 µm = 44.14 mm
- Electrode 4415 (right col, pos 2207) → (4415 // 2) × 20 µm = 44,140 µm = 44.14 mm

## Channel Allocation Algorithm

**Goal:** Given a depth range and column selection, select which channels to record and which bank to assign each.

### Phase 1: Bank Selection and Initial Assignment

1. Determine which banks span the target depth range (banks are spaced 3.84 mm apart: bank B covers depths B×3840 to B×3840+3830 µm)
2. For each available channel (based on column_selection), assign it to a bank using one of two strategies:

   - **Striped mode** (default, for even coverage):
     ```python
     assigned_bank = min_bank_needed + (i % num_banks_needed)
     ```
     Cycle through banks: ch0→B0, ch1→B1, ch2→B0, ch3→B1, ...
     Creates K interleaved grids with depth spacing K × pitch.

   - **Mixed mode** (for 'both' columns with local coupling):
     ```python
     assigned_bank = min_bank_needed + ((i // 2) % num_banks_needed)
     ```
     Pairs consecutive channels: (ch0, ch1)→B0, (ch2, ch3)→B1, ...

3. Filter channels to only those within the depth range
   - Electrode must satisfy: `depth_min ≤ electrode_depth ≤ depth_max`

### Phase 2: Gap Filling

Some channels may be excluded in Phase 1 if no electrode from that channel falls in the range. Phase 2 redistributes these missing channels:

1. Identify channels not yet selected
2. For each missing channel, find all valid banks where an electrode would fall in the depth range
3. Randomly pick one bank and add that channel/bank pair to the list

**Why random?** Distributes previously-excluded channels evenly across available banks to avoid clustering.

## Configuration Extraction

The reverse operation: given a channel list, infer the configuration parameters.

**`extract_config_from_channels(channel_list)`** returns:

```python
{
    'column_selection': 'even' | 'odd' | 'both',
    'assignment_mode': 'striped' | 'mixed',
    'ap_gain': int,
    'lf_gain': int,
    'ap_filter': bool,
    'ref_type': 'external' | 'tip',
    'ref_mode': 'own' | 'same' (if ref_type='tip'),
    'ref_bank': int (if ref_mode='same'),
    'depth_min_mm': float,
    'depth_max_mm': float
}
```

**Logic:**

- **Column selection**: Check which channels have odd/even IDs
- **Assignment mode** (if 'both' columns): Check if channels 0 and 1 share a bank
- **Depth range**: Min/max electrode ID × 0.02 mm
- **Reference**: Check if all ref_ids are 0 (external) or match banks (own/same)

## Public Interface

### 1. Generate IMRO from channel list

```python
channel_list = [
    (0, 1, 0, 500, 250, 1),
    (1, 1, 0, 500, 250, 1),
    ...
]
imro_content = ImroGenerator.generate_imro_content(channel_list)
# Returns: "(0,192)(0 1 0 500 250 1)(1 1 0 500 250 1)..."
```

### 2. Parse IMRO file content

```python
num_channels, channel_list = ImroGenerator.parse_imro_file(imro_content)
```

### 3. Generate channels by depth (high-level)

```python
channel_list = ImroGenerator.create_channel_list_by_depth(
    depth_min_mm=0.0,
    depth_max_mm=5.0,
    column_selection='both',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)
```

### 4. Extract configuration from channels

```python
config = ImroGenerator.extract_config_from_channels(channel_list)
```

## File Locations

| File | Role |
|------|------|
| `GUI/imro_generator.py` | Main `ImroGenerator` utility class |
| `Documentation/MD/imro_user_guide_A_tutorial.md` | User guide (how to use the tool) |
| `Documentation/MD/imro_dev_guide_B_howto.md` | Developer how-to (extending, recipes) |

## Design Decisions

### Why static class?

`ImroGenerator` contains no state — all methods are stateless utilities. Static methods emphasize this and avoid instantiation overhead.

### Why Phase 2 gap filling?

A naive Phase 1 approach might leave channels unused if their electrodes don't fall in the range. Phase 2 recovers these by finding alternative banks where each channel can be used, improving channel count and spatial distribution.

### Why randomization in Phase 2?

Deterministic bank assignment could cluster excluded channels. Shuffling distributes them evenly and reduces electrode clumping.

## Extension Points

### Add a new reference mode

Update `create_channel_list_by_depth()` to handle new `ref_type` / `ref_mode` combinations:

```python
elif ref_type == 'my_new_mode':
    if ref_mode == 'my_sub_mode':
        ref_id = ...
```

Update `extract_config_from_channels()` to recognize and reverse-engineer the new mode.

### Change bank spacing or probe geometry

Update probe constants at the top of the class:

```python
TOTAL_CHANNELS = 384
TOTAL_ELECTRODES = 4416
VIRTUAL_BANKS = 12
CHANNELS_PER_BANK = 384
```

If probe geometry changes (e.g., electrode spacing), update depth calculations.

### Add advanced channel sorting

After Phase 2 (line 218), sort or rearrange `channel_list` by a different criterion (e.g., depth-first rather than channel-ID-first).

## See Also

- [IMRO User Guide](imro_user_guide_A_tutorial.md) — user-facing workflows
- [IMRO How-To Guide](imro_dev_guide_B_howto.md) — recipes and common patterns
- Neuropixels specification: [https://www.neuropixels.org/](https://www.neuropixels.org/)
