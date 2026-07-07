# IMRO Neuropixels Generator
![Main Window](https://raw.githubusercontent.com/vitalylerner/imro-neuropixels/main/docs/img/mainwindow_mixed.jpg)

Neuropixels probe channel configuration tool. Create IMRO files for SpikeGLX/OpenEphys and export probe configurations for Kilosort.

**Problem:** The [OpenEphys Neuropixels Plugin](https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Neuropixels-PXI.html) can load [SpikeGLX IMRO](https://billkarsh.github.io/SpikeGLX/help/imroTables/) files but provides no tool to create them.

**Solution:** IMRO Generator lets you configure which electrodes to record from based on depth coverage, then export as IMRO files or [Kilosort probe dictionaries](https://kilosort.readthedocs.io/en/latest/tutorials/make_probe.html).

The GUI lets you:
- Choose your recording depth range (0–44.16 mm)
- Select assignment mode (Striped or Mixed) for uniform electrode distribution
- Configure gains, filters, and reference type
- Save IMRO files for OpenEphys/SpikeGLX
- Save JSON file for kilosort
- Load and modify existing IMRO configurations

## Installation
For an isolated environment, create a separate conda environment, any python>3.8 (for example, 3.11) and name it for example `imro`

```bash
$ conda -n imro python==3.11

$ conda activate imro 
```
Installation using pip
```bash
$ pip install imro-neuropixels
```

Run the gui
```bash
$ imro-gui
```
## Documentation
[Quick Start](QUICKSTART.md)
[Architecture](docs/ARCHITECTURE.md)
[Electrodes-channel assignment algorithm](docs/imro_algorithm.md)
[User Guide](docs/imro_user_guide_A_tutorial.md)

## Future directions

#### Multiple regions

Currently only one region defined by depth-min and depth-max is available. Need to add an option for multiple regions, for example 3 to 5 mm and 10 to 15 mm. 

#### Adding more probes. 
Currently works fine with a single [Neropixels1.0-NHP](https://www.neuropixels.org/probe-1-0-nhp-long) probe. The definitions are not hard-coded, but rather are defined in settings files. Need to add more probes to the settings/probes and test with other probes.

#### MRI pictures overlay
Don't have this functionality at the moment, but might be useful in future

## Example use

### Mapping 2cm from the tip up

example file `20mm.imro` in action, as seen in [`OpenEphys Probe Viewer`](https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Probe-Viewer.html), when flashes of light (2Hz) are shown to a fixating subject, while Neuropixels1.0-NHP is inserted in a visual area. 

![20mm](https://raw.githubusercontent.com/vitalylerner/imro-neuropixels/main/docs/img/oephys-probeview.jpg)

### Picking an active region for recording

![IMRO generator main window](https://raw.githubusercontent.com/vitalylerner/imro-neuropixels/main/docs/img/mainwindow_striped.jpg)

Set boundaries 10mm to 30mm

Map -> Save as IMRO 

Map -> Save kilosort probe

## Helpful Resources

- **[OpenEphys Neuropixels Plugin](https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Neuropixels-PXI.html)** — GUI for recording with Neuropixels probes, loads IMRO files
- **[SpikeGLX IMRO Format](https://billkarsh.github.io/SpikeGLX/help/imroTables/)** — Complete IMRO specification and format documentation
- **[Kilosort Probe Dictionary](https://kilosort.readthedocs.io/en/latest/tutorials/make_probe.html)** — Format for probe configurations in Kilosort4
- **[Neuropixels Probe 1.0 NHP](https://www.neuropixels.org/probe-1-0-nhp-long)** — Official probe specifications
