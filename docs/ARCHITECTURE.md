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

## Shared first step — find the banks that span the range

Both modes share the same first step, then differ only in how channels are spread across
banks.

- `B_start` = the lowest bank whose electrodes reach `depth_min`
- `B_end` = the highest bank whose electrodes reach into `depth_max`
- `K = B_end − B_start + 1` banks must be combined to cover the range

Because a single bank only spans ~7.64 mm, covering a wider range means combining several
banks — but each channel can be wired to only one bank at a time (see
[PROBE_FORMAT.md → Electrode-to-Channel Mapping](../imro_generator/settings/probes/PROBE_FORMAT.md#electrode-to-channel-mapping)).

**Every channel is always assigned to an in-range bank.** A channel first tries its
mode-assigned bank; if that electrode falls outside `[depth_min, depth_max]` it is moved
to the nearest in-range bank (within its allowed bank group). No channel is dropped, so
none is ever stranded on bank 0 at the tip. Channel 191 (a reference site in every bank)
is assigned like any other channel, so a full bank exports all 384 channels.

---

## Basic algorithm: mixed (interleaved — default)

Mixed mode mixes/interleaves the banks throughout the range with a single round-robin over
channel index:

```
for channel_id in 0 .. 383:
    assigned_bank = B_start + (channel_id mod K)
```

Both columns cycle through all `K` banks, so each column spans the entire depth range and
the two columns interleave in depth. This gives uniform two-column coverage across the
whole range — a uniform `K × 40 µm` grid whose near-optimality is derived in
[imro_algorithm.md → Optimal Analytical Solution](imro_algorithm.md#optimal-analytical-solution--interleaved-assignment).
This is the sensible default for a wide range.

---

## Basic algorithm: striped (single-column per region)

Striped mode splits the `K` banks into two contiguous stripes — the lower `ceil(K/2)`
banks for the even column, the upper `floor(K/2)` for the odd column — and round-robins
each column within its own stripe:

```
even_channels = 0, 2, 4, … , 382     # column 0 -> lower banks
odd_channels  = 1, 3, 5, … , 383     # column 1 -> upper banks

even_banks = [B_start .. B_start + ceil(K/2) - 1]
odd_banks  = [B_start + ceil(K/2) .. B_end]

bank(even_channels[i]) = even_banks[i mod len(even_banks)]
bank(odd_channels[i])  = odd_banks [i mod len(odd_banks)]
```

The even (left) column occupies the shallow banks and the odd (right) column the deep
banks, so each depth region is sampled by a single column — contiguous single-column
coverage over a longer span, at the cost of a lopsided layout for wide ranges. For `K == 2`
this reduces to even → `B_start`, odd → `B_start + 1`, reproducing
[examples/single_column.imro](../examples/single_column.imro). (When `K == 1` both columns
share the single bank, so striped and mixed coincide.)

Mode selection is the `assignment_mode` argument (`'mixed'` or `'striped'`, default
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
