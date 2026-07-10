# Quick Start Guide — IMRO Generator GUI


## Launch the GUI

Simply run:

```bash
imro-gui
```

The probe configuration window will open.

## Basic Workflow

1. **Set your recording depth range(s)**
   - The **Depth Ranges (mm)** table holds one row per range (Min, Max)
   - Use the icon buttons below the table: **＋** add a range, **−** remove the selected row, **✕** clear all
   - Add several rows to record from more than one window at once (e.g. 5–7 mm and 12–18 mm)
   - Each range also shows as a draggable green band on the probe view; drag it to adjust that row
   - The green electrodes show which channels will be recorded

2. **Choose assignment mode**
   - Select **Mixed** or **Striped** for how electrodes are distributed across depth
   - Mixed is recommended for uniform two-column coverage (and it is required for multiple ranges)
   - Optionally tick **Allow partial map (< 384 channels)** to export only in-range channels — leave it off for a fully-compatible 384-channel map
   - Click **Generate Channels** to update the visualization

3. **Configure recording settings**
   - Set **AP Gain** (typically 500)
   - Set **LF Gain** (typically 250)
   - Toggle **AP Filter** (ON recommended)
   - Choose reference type: **External** or **Tip (on-probe)**

4. **Save your configuration**
   - Go to **Map → Save IMRO** to save an IMRO file (`.imro` extension)
   - Use this file with OpenEphys or SpikeGLX
   - **Map → Save Kilosort Probe** exports probe layout as JSON

5. **Load previous configurations**
   - Go to **Map → Load IMRO** to open a saved IMRO file
   - The GUI will parse and restore all settings and visualization

## What is IMRO?

An IMRO file tells your recording system:
- Which **channels** are active (0–383)
- Which **depth** they record from (which bank)
- Reference electrode settings
- Gain and filter settings

## Need Help?

See the full documentation:
- `docs/imro_user_guide_A_tutorial.md` — Detailed step-by-step guide
- `docs/imro_algorithm.md` — Technical details about the algorithm
- `examples/` — Sample configuration files

## Troubleshooting

**"ImportError: No module named 'PyQt5'"**
- Install: `pip install PyQt5`

**"GUI doesn't appear on screen"**
- Try: `python -m imro_generator.gui.imro_config_gui`
- Or check your display/X server if on remote system

**"Changes not saving"**
- Ensure you have write permissions in the save directory
- Try saving to a different location
