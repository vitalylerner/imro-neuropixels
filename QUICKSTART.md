# Quick Start Guide — IMRO Generator GUI

**For end-users who want to configure Neuropixels NP1.0 probes.**

## Installation

```bash
pip install -e .
```

**Requires Python 3.8 or later.**

## Launch the GUI

Simply run:

```bash
imro-gui
```

The probe configuration window will open.

## Basic Workflow

1. **Set your recording depth**
   - Drag the red (min) and blue (max) cursor lines on the right to select your depth range
   - Or type values directly in the "Depth Range (mm)" fields
   - The green electrodes show which channels will be recorded

2. **Choose assignment mode**
   - Select **Striped** or **Mixed** for how electrodes are distributed across depth
   - Mixed is recommended for more uniform electrode distribution
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
