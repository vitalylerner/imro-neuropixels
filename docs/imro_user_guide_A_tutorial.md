# IMRO Generator — User Guide

Configure Neuropixels NP1.0 probe channel layouts and generate IMRO configuration files.

## What is IMRO?

An **IMRO file** specifies how channels are configured on a Neuropixels NP1.0 probe:
- Which **channels** (0–383) are active
- Which **bank** each channel reads from (the physical location on the probe shaft, determines depth)
- **Reference** electrode for each channel (external ground or another channel)
- **Gain** settings for AP (action potential) and LF (local field potential) bands
- **Filter** state for the AP band

IMRO files are text files in a single-line format used by OpenEphys and SpikeGLX.

## Quick Start

### Step 1: Launch the IMRO Generator GUI

After installing the imro-generator package, you can launch the GUI in several ways:

**Option A: Command line (easiest)**
```bash
imro-gui
```

**Option B: Python**
```python
from imro_generator import main
main()
```

**Option C: Direct Python execution**
```python
from imro_generator import ImroConfigGUI
import sys
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
window = ImroConfigGUI()
window.show()
sys.exit(app.exec_())
```

The IMRO Config GUI window will open with an interactive probe visualization showing all 4416 electrode sites.

### Step 2: Select Probe Configuration

Use the **Assignment Mode** selector to choose how electrodes are distributed:
- **Mixed mode** (recommended): banks are interleaved throughout the range, so both columns span the whole depth range — uniform two-column coverage
- **Striped mode**: the two columns form separate stripes (even column = shallow banks, odd column = deep banks), giving single-column coverage per depth region

### Step 3: Define Your Recording Depth Range(s)

The **Depth Ranges (mm)** table holds one row per range, each with a **Min** and
**Max** in mm (e.g. 0 mm = tip of probe, 5 mm = 5 mm from tip). Edit the cells
directly, or drag the corresponding green band on the probe view.

Icon buttons below the table:
- **＋** — add a range
- **−** — remove the selected row
- **✕** — clear all rows

Add several rows to record from more than one window at once — "virtual banks",
e.g. 5–7 mm together with 12–18 mm. Multiple ranges require **Mixed** mode (see
Step 4); each range is covered uniformly in both columns.

The NP1.0 probe is 44.16 mm long total, with 4416 electrodes in 2 columns (odd/even alternating), spaced 20 µm vertically within each column and 103 µm horizontally between columns.

### Step 4: Choose Bank Assignment Strategy

How to distribute channels across banks (physical groups along the shaft):

- **Mixed mode** (default): channel `c` → bank `B_start + (c mod K)`, a single round-robin over all K banks
  - Both columns span the full depth range, interleaved
  - Uniform two-column coverage — the sensible default for a wide range

- **Striped mode**: the K banks are split into two stripes — even column (0, 2, 4, …) fills the lower banks, odd column (1, 3, 5, …) the upper banks
  - Each depth region is sampled by a single column
  - For a two-bank range this reproduces `examples/single_column.imro`

**Allow partial map (< 384 channels):** an NP1.0 probe always records on all 384
channels, so by default every channel is assigned — any channel that cannot reach
a requested range is parked on the nearest bank (it will appear just outside your
range in the probe viewer). For narrow ranges this can be many channels. Tick
**Allow partial map** to instead export only the channels that land inside a range
(the header count drops below 384). OpenEphys loads a partial map, but its probe
viewer may render the unlisted channels oddly — leave the option off for maximum
compatibility.

### Step 5: Set Gain and Filter

- **AP Gain**: Amplification for action potentials (e.g., 500–1000x typical)
- **LF Gain**: Amplification for slow potentials (e.g., 250x typical)
- **AP Filter**: Enable high-pass filtering on the AP band (recommended: ON)

### Step 6: Choose Reference Electrode

Select your reference electrode type:

**External reference** (standard):
- All channels reference to an external ground electrode
- Cleanest setup, no cross-talk between channels

**Tip (on-probe) reference**:
- Reference to probe tip or another on-shank location
- Each channel uses its own bank's reference electrode

### Step 7: Generate and Save IMRO File

Click **Generate Channels** to create the configuration. The green electrodes on the probe visualization will update to show your selection.

**Save to disk**:
- Go to **Map → Save IMRO** in the menu
- Choose where to store the `.imro` file (typically alongside your experiment folder)

**Export probe layout**:
- Go to **Map → Save Kilosort Probe** to export as JSON format

## Understanding the IMRO Format

An IMRO file looks like:

```
(0,192)(0 1 0 500 250 1)(1 1 0 500 250 1)(2 1 0 500 250 1)...(191 11 0 500 250 1)
```

Breaking it down:
- `(0,192)` — Probe type 0 (NP1.0), 192 channels
- `(ch_id bank ref_id ap_gain lf_gain ap_filter)` — one tuple per channel
  - `ch_id`: channel number (0–191)
  - `bank`: which 384-electrode bank (0–11)
  - `ref_id`: reference electrode (0 = external)
  - `ap_gain`: AP band gain (500, 1000, etc.)
  - `lf_gain`: LF band gain (250, etc.)
  - `ap_filter`: filter on (1) or off (0)

## Typical Workflows

### Recording from a single depth layer

**Goal:** Record from channels at ~10 mm depth.

1. Set **Minimum depth** = 9.9 mm
2. Set **Maximum depth** = 10.1 mm
3. Use **Mixed mode** (a narrow range falls in one bank, so both modes behave the same here — both columns are recorded)
4. Generate Channels

Result: Channels clustered near 10 mm depth.

### Recording across multiple depths

**Goal:** Record from 0–5 mm continuously.

1. Set **Minimum depth** = 0 mm
2. Set **Maximum depth** = 5 mm
3. Use **Mixed mode** for uniform electrode spacing
4. Generate Channels

Result: Channels spanning all 5 mm with balanced distribution.

### High-resolution recording with mixed mode

**Goal:** Record densely with better electrode spacing.

1. Set your desired **Depth range**
2. Use **Mixed mode** (default)
3. Generate Channels

Result: Even/odd column interleaving for optimal spatial sampling.

## Importing an Existing IMRO File

If you have a pre-configured IMRO file and want to inspect or modify it:

1. Go to **Map → Load IMRO** in the menu
2. Select your `.imro` file
3. The generator will extract and display:
   - Detected **depth range** (inferred from channel positions)
   - **Assignment mode** (striped or mixed)
   - **Reference type** and gains
   - **Filter state**

You can then modify any setting and regenerate.

## Troubleshooting

### "No valid channels in depth range"

The depth range you specified doesn't match any available channels. 
- Check that **min_depth < max_depth**
- Ensure depths are in mm (0–44.16)
- Verify your range includes electrodes within the probe

### "Expected N channels, found M"

The IMRO file format is invalid or corrupted. Re-export from the probe configuration tool (OpenEphys, SpikeGLX).

### Depth calculation seems off

Depth is determined from electrode position in the CSV. Each electrode has a Y-coordinate in micrometers.
- Electrode 0 (top) → 0 µm
- Electrode 2 → 20 µm (one row down)
- Electrode 4414/4415 (bottom) → ~44,140 µm (44.14 mm)

## See Also

- [IMRO Developer Guide](imro_dev_guide_A_overview.md) — algorithm details, channel allocation strategy
- [Slice GUI Guide](ephys_slice_guide.md) — using IMRO files in spike slicing
- Neuropixels documentation: [https://www.neuropixels.org/](https://www.neuropixels.org/)
