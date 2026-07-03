# IMRO Generator


When [`Neurpixels probes`](https://www.neuropixels.org/probe-1-0-nhp-long) are used with [`OpenEphys`](https://github.com/open-ephys), a challenge of creating channel map arises.  The [`Neurpixels plugin`](https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Neuropixels-PXI.html)allows to load SpixeGLX-native[`IMRO`](https://billkarsh.github.io/SpikeGLX/help/imroTables/) files but suggests no plugin for creating them. IMRO-generator is oriented for creating the IMRO files based on depth coverage, and exporting the tables to [`kilosort`](https://github.com/MouseLand/kilosort) [`probe description in JSON format`](https://kilosort.readthedocs.io/en/latest/tutorials/make_probe.html)
![IMRO generator main window](imro_generator/mainwindow_striped.jpg)
## Installation

**New to probe configuration?** Start here:

1. **Install**: `pip install -e .` (requires Python 3.8+)
2. **Launch**: `imro-gui`
3. **Quick guide**: See [`QUICKSTART.md`](QUICKSTART.md)

The GUI lets you:
- Choose your recording depth range (0–44.16 mm)
- Select assignment mode (Striped or Mixed) for uniform electrode distribution
- Configure gains, filters, and reference type
- Save IMRO files for OpenEphys/SpikeGLX
- Load and modify existing IMRO configurations

## For Developers

**Integrating into your software?** See:

- [`DEVELOPERS.md`](DEVELOPERS.md) — Architecture, setup, extending
- `docs/imro_algorithm.md` — Algorithm specification
- `docs/imro_dev_guide_A_overview.md` — Detailed architecture
- `tests/` — Test suite with examples

## System Requirements

- **Python**: 3.8 or later
- **GUI dependencies**: PyQt5, pyqtgraph (installed automatically)
- **Data processing**: NumPy (installed automatically)

## Installation

```bash
# Standard installation
pip install -e .

# With development tools
pip install -e ".[dev]"  # (if extras defined in setup.py)

# From source (if cloning)
git clone <repo-url>
cd imro-generator
pip install -e .
```

## Example use
![IMRO generator main window](imro_generator/mainwindow_striped.jpg)

Set boundaries 10mm to 30mm

Map -> Save as IMRO 

Map -> Save kilosort probe
