# Project Architecture

This document describes how the project represents a probe, how it decides which
electrodes to record from, and the two output formats it produces. It references the
existing specifications rather than repeating them — read
[PROBE_FORMAT.md](../imro_generator/settings/probes/PROBE_FORMAT.md) for the full
geometry spec and [imro_algorithm.md](imro_algorithm.md) for the formal derivation of
the assignment algorithm.

Data flow at a glance:

```
probe files (CSV/JSON)  ──►  ImroGenerator  ──►  electrode list  ──►  .imro  (SpikeGLX/OpenEphys)
                                                                └──►  .json  (Kilosort4)
```

The engine lives in `imro_generator/core/imro_generator.py`; the GUI in
`imro_generator/gui/imro_config_gui.py` is a thin front end over it.

---

## Files describing the probe

All probe definitions live under
[imro_generator/settings/probes/](../imro_generator/settings/probes/). Each probe is a
sub-folder (currently
[npx1.0-nhp/](../imro_generator/settings/probes/npx1.0-nhp/)) plus two shared files.

| File | Purpose |
|------|---------|
| [`<probe>/channelmap.csv`](../imro_generator/settings/probes/npx1.0-nhp/channelmap.csv) | The authoritative electrode geometry — one row per electrode. The columns (`electrode, channel, bank, row, col, x, y, ref`) are documented in [PROBE_FORMAT.md](../imro_generator/settings/probes/PROBE_FORMAT.md#channel-map-format). This is the single source of truth the engine reads. |
| [`<probe>/probe.json`](../imro_generator/settings/probes/npx1.0-nhp/probe.json) | Probe metadata: display `name`, `probe_type`, and `imro-format`. The GUI lists a folder as a selectable probe only if it contains this file. |
| [`probes.csv`](../imro_generator/settings/probes/probes.csv) | Maps every Neuropixels `probe_type` / part number to its IMRO format family (`imro_np1000`, `imro_np2000`, …). Used to interpret the numeric header of imported IMRO files. |
| [PROBE_FORMAT.md](../imro_generator/settings/probes/PROBE_FORMAT.md) | Human-readable geometry specification for NP1.0-NHP: key parameters, electrode↔channel mapping, reference electrodes, and the IMRO field definitions. |

At start-up the engine loads the geometry once into a pandas DataFrame and derives its
specs (total electrodes, channels, banks, max depth) from the CSV — nothing about the
geometry is hard-coded. See
[PROBE_FORMAT.md → Key Specifications](../imro_generator/settings/probes/PROBE_FORMAT.md#key-specifications)
for the NP1.0-NHP values (4,416 electrodes, 384 channels, 12 banks, 20 µm row pitch).

**Adding a probe:** drop a new folder with a `channelmap.csv` and `probe.json`; if it
uses a new IMRO format, add its rows to `probes.csv`.

---

## Basic algorithm: striped

Both modes share the same first step, then differ only in how channels are spread across
banks.

**Shared step — find the banks that span the requested depth range:**

- `B_start` = the lowest bank whose electrodes reach `depth_min`
- `B_end` = the highest bank whose electrodes reach into `depth_max`
- `K = B_end − B_start + 1` banks must be interleaved to cover the range

Because a single bank only spans ~7.64 mm, covering a wider range means combining several
banks — but each channel can be wired to only one bank at a time (see
[PROBE_FORMAT.md → Electrode-to-Channel Mapping](../imro_generator/settings/probes/PROBE_FORMAT.md#electrode-to-channel-mapping)).

**Striped assignment:**

```
for channel_id in 0 .. 383:
    assigned_bank = B_start + (channel_id mod K)
```

A single round-robin walks the channels in natural order (0, 1, 2, 3, …) and cycles them
through the `K` banks. Each (channel, bank) pair is then resolved to a non-reference
electrode and kept only if its depth falls inside `[depth_min, depth_max]`.

Because a channel's *column* is just its parity (even = column 0, odd = column 1), a
plain round-robin over channel index moves both columns through the bank cycle **in the
same phase**. The two columns therefore land at the same depths, producing the horizontal
**stripes** of active sites you see in
[the striped view](img/mainwindow_striped.jpg). The interleaving still gives a uniform
`K × 40 µm` grid within the range — the near-optimality of this scheme is derived in
[imro_algorithm.md → Optimal Analytical Solution](imro_algorithm.md#optimal-analytical-solution--interleaved-assignment).

---

## Basic algorithm: mixed

Mixed mode uses the same bank range (`B_start`, `K`) but treats the two columns
separately and offsets their bank cycles by half a period:

```
even_channels = 0, 2, 4, … , 382     # column 0
odd_channels  = 1, 3, 5, … , 383     # column 1

for i in 0 .. 191:
    bank(even_channels[i]) = B_start + ( i          mod K)
    bank(odd_channels[i])  = B_start + ((i + K//2)  mod K)
```

The `K//2` phase shift on the odd (right) column staggers it against the even (left)
column, so the two columns' selected electrodes **interleave in depth** instead of
aligning. The result is the denser, checkerboard-like coverage of
[the mixed view](img/mainwindow_mixed.jpg) — the same per-column pitch as striped, but the
columns fill each other's gaps, roughly halving the effective vertical spacing across the
shank. (When `K == 1` the offset is disabled and mixed degenerates to striped.)

Mode selection is the `assignment_mode` argument (`'striped'` or `'mixed'`, default
`'mixed'`); everything downstream — filtering, IMRO export, JSON export — is identical.

---

## IMRO file structure

The `.imro` file is the SpikeGLX/OpenEphys channel-configuration format. Its header and
per-channel fields are fully specified in
[PROBE_FORMAT.md → IMRO Format](../imro_generator/settings/probes/PROBE_FORMAT.md#imro-format);
in short:

```
(NP1000,384)                       ← header: (format/type, channel count)
(ChannelID,Bank,Reference,APgain,LFgain,Filter)   ← one entry per channel
```

The engine emits one entry per channel that owns a selected electrode, using that
electrode's bank; the reference field is mapped from the GUI choice
(`external → 0`, `tip → 1`, `on_shank → 2`). On import it accepts both on-disk variants
found in real files:

- multi-line, comma-separated — see [examples/20mm.imro](../examples/20mm.imro)
- single-line, space-separated — see [examples/single_column.imro](../examples/single_column.imro)

The numeric header form (e.g. `(0,384)` or `(1020,384)`) is resolved to an IMRO family
via [`probes.csv`](../imro_generator/settings/probes/probes.csv).

**External reference:**
[SpikeGLX IMRO table specification](https://billkarsh.github.io/SpikeGLX/help/imroTables/).

---

## JSON file structure

The `.json` file is a [Kilosort4 probe dictionary](https://kilosort.readthedocs.io/en/latest/tutorials/make_probe.html).
It contains one entry per selected electrode, in CSV row order:

| Key | Type | Meaning |
|-----|------|---------|
| `chanMap` | `int[]` | Recording channel index for each selected site (`channel` column) |
| `xc` | `float[]` | X-coordinate in µm (`x` column: 0 or 103) |
| `yc` | `float[]` | Y / depth coordinate in µm (`y` column) |
| `kcoords` | `int[]` | Shank/group index — here the electrode's `bank` |
| `n_chan` | `int` | Number of selected sites (length of the arrays above) |

All values are plain lists so the dictionary is directly JSON-serializable and loads into
Kilosort4 without conversion. A generated example is
[examples/20mm.json](../examples/20mm.json).

**External reference:**
[Kilosort — Making a probe dictionary](https://kilosort.readthedocs.io/en/latest/tutorials/make_probe.html).
