# Known Issues

## #1 — OpenEphys shows all electrodes at the tip after import (FIXED)

**Status:** Fixed 2026-07-08 in `ImroGenerator.generate_imro_content`.

### Symptom

After exporting a `.imro` file and loading it in OpenEphys, every channel showed
an electrode closest to the tip (lowest electrode/bank numbers), regardless of the
depth range that was selected in the GUI.

### Root cause

The exported file was **malformed** for OpenEphys/SpikeGLX. When OpenEphys fails to
parse an IMRO table it silently falls back to its default map — all channels on
bank 0, i.e. the electrodes closest to the tip. That default is exactly what the
user saw.

Three separate deviations from the format documented in
[`imro_user_guide_A_tutorial.md`](imro_user_guide_A_tutorial.md) (§"Understanding
the IMRO Format") caused the parse failure:

| # | Old (broken) output | Required format |
|---|---------------------|-----------------|
| 1 | Header `(NP1000,384)` — a non-numeric string | Numeric probe type, e.g. `(0,384)` |
| 2 | Comma-separated fields: `(6,1,1,500,250,1)` | Space-separated: `(6 1 1 500 250 1)` |
| 3 | One entry only per in-range channel (e.g. 311 of 384) while the header claimed 384 | Exactly `num_channels` entries — **every** channel defined |
| 4 | Multi-line (`\n`-joined) | Single line (canonical SpikeGLX form) |

Issue #3 was the most damaging: a narrow depth range (e.g. 5–6 mm) produced as few
as 101 entries under a header claiming 384, guaranteeing rejection.

The bug was invisible to the tool's own round-trip because `parse_imro_file`
tolerantly accepts comma- **or** space-separated entries, multi-line **or**
single-line, and partial files. OpenEphys is strict.

### Fix

`generate_imro_content` now emits:

```
(0,384)(0 0 1 500 250 1)(1 0 1 500 250 1)...(383 2 1 500 250 1)
```

- Numeric probe-type header (`probe_type=0`, configurable).
- Space-separated fields, single line.
- An entry for **every** channel. OpenEphys has no "disabled channel" concept, so
  any channel not covered by the selected depth range is parked on bank 0 (its tip
  electrode). This is a deliberate, valid choice — the selected channels sit at the
  requested depth; the remainder read their bank-0 electrode.

The output format was validated against a known-good, OpenEphys-accepted file,
[`examples/single_column.imro`](../examples/single_column.imro): header `(0,384)`,
space-separated fields, single line, all 384 channels present.

## #2 — Cannot produce a full bank; channel 191 always parked on bank 0 (FIXED)

**Status:** Fixed 2026-07-10 in `_get_electrode_in_bank` and `parse_imro_file`.

### Symptom

Generating a configuration for the full depth range of a single bank (e.g. bank 1,
3840–7660 µm, mixed mode) produced 383 channels on that bank and **channel 191 on
bank 0**, instead of all 384 channels on the selected bank. It was impossible to
reproduce a "full bank" file such as one exported by OpenEphys.

### Root cause

On this probe **channel 191 is a reference site in every bank** (the 12 reference
electrodes 191, 575, 959, … all map to channel 191). Both
`_get_electrode_in_bank` and `parse_imro_file` filtered rows with
`ref == False`, so channel 191 was never assigned to any bank. In the electrode-list
representation it therefore had no entry, and `generate_imro_content` fell back to
parking it on bank 0.

OpenEphys assigns **all 384 channels** to the selected bank regardless of the
reference flag — see the reference files `examples/single_column.imro` (channel 191
→ bank 1) and the bank-1 export used to validate this fix (`(191 1 0 500 250 1)`).

### Fix

Removed the `ref == False` filter from bank assignment (`_get_electrode_in_bank`)
and from the parse-time channel→electrode lookup (`parse_imro_file`). Channel 191 is
now assigned to the requested bank like any other channel. Verified: generating the
full bank-1 range in mixed mode now produces an **exact byte-for-byte match** with
the OpenEphys-exported bank-1 file, and matches `single_column.imro`'s channel→bank
map exactly (entry ordering differs but is irrelevant — each tuple carries its own
channel id).

Note: the reference site still renders grey (not green) in the GUI, since the
visualization checks the `ref` flag before the selection set.

## #3 — Channels stranded at the tip for any range not starting at bank 0 (FIXED)

**Status:** Fixed 2026-07-10 in `generate_electrode_list`.

### Symptom

A configuration for e.g. 5–18 mm loaded into OpenEphys showed a dense clump of
channels at the very tip (0–3.8 mm) plus lopsided columns — "crap". Re-exporting
from OpenEphys produced a channel→bank map **byte-identical** to the generated
file, proving OpenEphys parsed it correctly; the configuration itself was wrong.

### Root cause

`generate_electrode_list` assigned each channel a bank by position
(`b_start + channel % K`) and then **discarded** any channel whose electrode fell
outside `[depth_min, depth_max]`. `generate_imro_content` then parked every
discarded channel on bank 0 (the tip). For a 5–18 mm range this stranded 59
channels at the tip, even though every one of the 384 channels had a valid
in-range bank available (banks are 7.68 mm apart; a 13 mm range always contains at
least one electrode per channel).

### Fix

`generate_electrode_list` now assigns **every** channel to an in-range bank: the
round-robin bank if its electrode is in range, otherwise the nearest in-range bank
(within the channel's allowed bank group), and only as a last resort the bank
nearest the range. No channel is dropped, so nothing is stranded on bank 0.
Verified for 5–18 mm: 0 channels on bank 0, full coverage 5.00–17.98 mm, max gap
60 µm (striped) / 40 µm (mixed). The single-bank (`bank2.imro`) and two-bank
(`single_column.imro`) reference cases are unchanged.

## #4 — "mixed" and "striped" labels were swapped (FIXED)

**Status:** Fixed 2026-07-10 in `generate_electrode_list` and
`_infer_assignment_mode`.

The behaviors were attached to the wrong names:

- **mixed** should mean banks are *mixed / interleaved* throughout the range
  (round-robin, both columns spanning the whole range — uniform two-column
  coverage).
- **striped** should mean the two columns form separate *stripes* (even column =
  lower banks, odd column = upper banks — single-column per depth region, as in
  `examples/single_column.imro`).

Previously the round-robin behavior was labeled 'striped' and the single-column
behavior 'mixed'. The labels are now swapped so each matches its meaning. The GUI
radios ("Mixed" default, "Striped") required no change — they pass the mode string
of the same name, which now selects the correct behavior. `_infer_assignment_mode`
(used to restore the radio on Load IMRO) was rewritten to match: it reports
'striped' when the columns occupy ordered-disjoint bank blocks
(`max(even) < min(odd)`), else 'mixed'.

### Choosing a mode for wide ranges

For a range spanning many banks, **mixed** gives uniform two-column coverage (both
columns span the range, interleaved) and is the sensible default. **striped**
gives single-column-per-region: the left column covers the shallow half and the
right column the deep half — correct by design but not what you want for uniform
wide-range recording.

Docs updated to match: `docs/ARCHITECTURE.md`, `docs/imro_user_guide_A_tutorial.md`,
`PROBE_FORMAT.md` (also corrected to the space-separated `(0,384)` format and 12
banks). `docs/imro_algorithm.md` is a theoretical derivation of the interleaved
(mixed) scheme and does not use the mode labels; its step-3 "drop out-of-range
channels" no longer matches the code (channels are now reassigned in-range, per
issue #3) but the uniformity analysis still holds.

### Open question — probe type vs. bank count

This is a 45 mm NHP probe with **12 banks (0–11)**, but a standard NP1.0 probe
(type `0`) is usually described as having only banks 0–2. In practice, header
`(0,384)` **works** in the OpenEphys build in use here — OpenEphys detects the
physical probe type from the hardware and applies the per-channel bank assignments
regardless of the header's declared type. If a future OpenEphys/SpikeGLX version
rejects banks > 2 under type 0, pass the probe's real type code to
`generate_imro_content(..., probe_type=<code>)` (e.g. `1030` for the NP1030-series
NHP probes; see `settings/probes/probes.csv`).

### Follow-up cleanup (not blocking)

- `PROBE_FORMAT.md` still documents the old comma-separated `(NP1000,384)` format
  and states "Bank 0-1 (NP1.0 has 2 banks)" — both are wrong for this probe and
  should be updated to match the shipped format.
- `tests/test_assignment_modes.py` calls `create_channel_list_by_depth` /
  `extract_config_from_channels`, which no longer exist on `ImroGenerator`
  (current API is `generate_electrode_list` / `generate_imro_content` /
  `parse_imro_file`). The tests do not run against the current code.
