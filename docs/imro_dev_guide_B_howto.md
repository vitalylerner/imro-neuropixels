# IMRO Generator — Developer Guide (How-To)

Recipes and patterns for working with the `ImroGenerator` class.

## Recipe: Generate channels for a specific depth layer

**Goal:** Select all channels that reach a specific depth (e.g., 10 mm).

```python
from GUI.imro_generator import ImroGenerator

# Record around 10 mm ± 0.1 mm tolerance
depth_min_mm = 9.9
depth_max_mm = 10.1

channel_list = ImroGenerator.create_channel_list_by_depth(
    depth_min_mm=depth_min_mm,
    depth_max_mm=depth_max_mm,
    column_selection='both',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)

print(f"Found {len(channel_list)} channels at {depth_min_mm}–{depth_max_mm} mm")
for ch_id, bank, ref_id, ap_gain, lf_gain, ap_filter in channel_list:
    electrode_id = ch_id + bank * 384
    depth_mm = electrode_id * 20 / 1000
    print(f"  Channel {ch_id:3d}, Bank {bank:2d}, Depth {depth_mm:7.2f} mm")
```

## Recipe: Create a high-density probe configuration

**Goal:** Record from the maximum number of channels across a depth range.

```python
channel_list = ImroGenerator.create_channel_list_by_depth(
    depth_min_mm=0.0,
    depth_max_mm=5.0,
    column_selection='both',        # Use all 384 channels
    assignment_mode='striped',      # Even distribution
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)

# Generate IMRO file
imro_content = ImroGenerator.generate_imro_content(channel_list)

# Save to disk
with open('my_probe_config.imro', 'w') as f:
    f.write(imro_content)

print(f"Saved {len(channel_list)} channels to my_probe_config.imro")
```

## Recipe: Create a paired-column configuration

**Goal:** Keep neighboring columns (0, 1), (2, 3), ... in the same bank for spike sorting correlation.

```python
channel_list = ImroGenerator.create_channel_list_by_depth(
    depth_min_mm=0.0,
    depth_max_mm=5.0,
    column_selection='both',
    assignment_mode='mixed',        # Pairs same bank
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)

# Verify pairing
print("Channel pairs per bank:")
for bank in range(12):
    channels_in_bank = [ch for ch, b, _, _, _, _ in channel_list if b == bank]
    print(f"  Bank {bank}: channels {sorted(channels_in_bank)}")
```

## Recipe: Use tip referencing

**Goal:** Reference all channels to their own bank's tip electrode.

```python
channel_list = ImroGenerator.create_channel_list_by_depth(
    depth_min_mm=0.0,
    depth_max_mm=5.0,
    column_selection='both',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='tip',
    ref_mode='own'  # Each channel → its own bank's reference
)

# Verify each channel references its own bank
for ch_id, bank, ref_id, _, _, _ in channel_list:
    assert ref_id == bank, f"Channel {ch_id} should reference bank {bank}, got {ref_id}"
```

## Recipe: Parse and inspect an IMRO file

**Goal:** Load an existing IMRO file and understand its configuration.

```python
from GUI.imro_generator import ImroGenerator

# Read IMRO file
with open('my_existing_config.imro', 'r') as f:
    imro_content = f.read()

# Parse
num_channels, channel_list = ImroGenerator.parse_imro_file(imro_content)

# Extract configuration
config = ImroGenerator.extract_config_from_channels(channel_list)

print(f"Channels: {num_channels}")
print(f"Columns: {config['column_selection']}")
print(f"Assignment: {config['assignment_mode']}")
print(f"Depth range: {config['depth_min_mm']:.2f} – {config['depth_max_mm']:.2f} mm")
print(f"Reference: {config['ref_type']} (mode: {config.get('ref_mode', 'N/A')})")
print(f"AP Gain: {config['ap_gain']}, LF Gain: {config['lf_gain']}")
print(f"AP Filter: {'ON' if config['ap_filter'] else 'OFF'}")
```

## Recipe: Modify a probe configuration

**Goal:** Load an existing IMRO, change the gain, and save.

```python
from GUI.imro_generator import ImroGenerator

# Parse existing
with open('my_existing_config.imro', 'r') as f:
    imro_content = f.read()

num_channels, channel_list = ImroGenerator.parse_imro_file(imro_content)

# Modify: change AP gain to 1000
new_channel_list = [
    (ch_id, bank, ref_id, 1000, lf_gain, ap_filter)
    for ch_id, bank, ref_id, ap_gain, lf_gain, ap_filter in channel_list
]

# Generate and save
new_imro = ImroGenerator.generate_imro_content(new_channel_list)
with open('my_modified_config.imro', 'w') as f:
    f.write(new_imro)

print("Saved modified config with AP gain = 1000")
```

## Recipe: Compare two IMRO files

**Goal:** Check if two configs differ in channel count, gains, or reference.

```python
from GUI.imro_generator import ImroGenerator

def compare_imro_files(path1, path2):
    with open(path1) as f1, open(path2) as f2:
        imro1, imro2 = f1.read(), f2.read()
    
    _, ch_list1 = ImroGenerator.parse_imro_file(imro1)
    _, ch_list2 = ImroGenerator.parse_imro_file(imro2)
    
    config1 = ImroGenerator.extract_config_from_channels(ch_list1)
    config2 = ImroGenerator.extract_config_from_channels(ch_list2)
    
    print(f"Channel count: {len(ch_list1)} vs {len(ch_list2)}")
    print(f"Depth range: {config1['depth_min_mm']:.2f}–{config1['depth_max_mm']:.2f} mm "
          f"vs {config2['depth_min_mm']:.2f}–{config2['depth_max_mm']:.2f} mm")
    print(f"AP Gain: {config1['ap_gain']} vs {config2['ap_gain']}")
    print(f"Reference: {config1['ref_type']} vs {config2['ref_type']}")
    
    if imro1 == imro2:
        print("✓ Files are identical")
    else:
        print("✗ Files differ")

compare_imro_files('config_a.imro', 'config_b.imro')
```

## Recipe: Generate channels for even vs. odd columns

**Goal:** Create separate configs for even and odd columns and compare coverage.

```python
from GUI.imro_generator import ImroGenerator

depth_min, depth_max = 0.0, 5.0

# Even columns
even_channels = ImroGenerator.create_channel_list_by_depth(
    depth_min_mm=depth_min,
    depth_max_mm=depth_max,
    column_selection='even',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)

# Odd columns
odd_channels = ImroGenerator.create_channel_list_by_depth(
    depth_min_mm=depth_min,
    depth_max_mm=depth_max,
    column_selection='odd',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)

# Both
both_channels = ImroGenerator.create_channel_list_by_depth(
    depth_min_mm=depth_min,
    depth_max_mm=depth_max,
    column_selection='both',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)

print(f"Even columns: {len(even_channels)} channels")
print(f"Odd columns: {len(odd_channels)} channels")
print(f"Both columns: {len(both_channels)} channels")
```

## Recipe: Generate multiple IMRO files for a multi-shank experiment

**Goal:** Create separate IMRO configs for N probes, each with a different depth offset.

```python
from GUI.imro_generator import ImroGenerator

num_probes = 4
depth_offsets = [0.0, 1.0, 2.0, 3.0]  # mm

for probe_id, offset in enumerate(depth_offsets):
    channel_list = ImroGenerator.create_channel_list_by_depth(
        depth_min_mm=0.0 + offset,
        depth_max_mm=5.0 + offset,
        column_selection='both',
        assignment_mode='striped',
        ap_gain=500,
        lf_gain=250,
        ap_filter=True,
        ref_type='external'
    )
    
    imro_content = ImroGenerator.generate_imro_content(channel_list)
    
    filename = f'probe_{probe_id:02d}_offset_{offset:.1f}mm.imro'
    with open(filename, 'w') as f:
        f.write(imro_content)
    
    print(f"Saved {filename}: {len(channel_list)} channels")
```

## Recipe: Validate channel allocation coverage

**Goal:** Check that selected channels provide continuous or near-continuous depth coverage.

```python
from GUI.imro_generator import ImroGenerator

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

# Collect all depths
depths_um = []
for ch_id, bank, _, _, _, _ in channel_list:
    electrode_id = ch_id + bank * 384
    # Depth depends on position in column (accounting for alternating odd/even)
    depth_um = (electrode_id // 2) * 20  # 20 µm vertical spacing
    depths_um.append(depth_um)

depths_um.sort()

# Check max gap
gaps = [depths_um[i+1] - depths_um[i] for i in range(len(depths_um)-1)]
max_gap_um = max(gaps) if gaps else 0
max_gap_mm = max_gap_um / 1000

print(f"Coverage: {len(depths_um)} electrodes from {depths_um[0]/1000:.2f} to {depths_um[-1]/1000:.2f} mm")
print(f"Maximum gap: {max_gap_um} µm ({max_gap_mm:.2f} mm)")

if max_gap_um > 100:
    print("⚠ Warning: Large gap detected; consider striped mode or reducing depth range")
```

## Troubleshooting

### Q: My channel list is empty

**A:** The depth range doesn't match any electrodes.
- Check: `depth_min < depth_max` and both are in 0–44.16 mm
- Verify column selection includes enough channels for the probe geometry
- Try wider depth range (e.g., ±1 mm)

### Q: Why does my parsed config show different banks than expected?

**A:** Phase 2 gap-filling re-assigns channels. This is intentional to maximize coverage.
- Use `create_channel_list_by_depth()` directly for deterministic output
- If you need exact bank assignments, avoid the convenience method and build channel_list manually

### Q: How do I reduce noise / cross-talk?

**A:** Use external referencing + keep columns in separate banks:
- `ref_type='external'`
- `column_selection='even'` or `'odd'` (not 'both')
- `assignment_mode='striped'` (not 'mixed')

### Q: Can I use the same IMRO file for multiple recordings?

**A:** Yes, as long as the probe position and reference electrode don't change.
- Document the file with metadata: depth, experiment ID, date
- Save IMRO files alongside your experiment folder for tracking

## See Also

- [IMRO Overview](imro_dev_guide_A_overview.md) — algorithm details, design rationale
- [IMRO User Guide](imro_user_guide_A_tutorial.md) — user-facing workflows
- Source code: `GUI/imro_generator.py`
