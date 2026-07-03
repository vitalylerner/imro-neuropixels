#!/usr/bin/env python3
"""Test the depth-based channel selection algorithm."""

from imro_generator.core.imro_generator import ImroGenerator

def analyze_channel_list(gen, channel_list, depth_min_mm, depth_max_mm):
    """Analyze and visualize the selected channels."""
    print(f"\n{'='*70}")
    print(f"Depth Range: {depth_min_mm:.2f} - {depth_max_mm:.2f} mm")
    print(f"Depth Range: {depth_min_mm*1000:.0f} - {depth_max_mm*1000:.0f} µm")
    print(f"{'='*70}")

    if not channel_list:
        print("No channels selected!")
        return

    # Group by bank
    banks = {}
    for ch_id, bank, ref_id, ap_gain, lf_gain, ap_filter in channel_list:
        if bank not in banks:
            banks[bank] = []
        banks[bank].append(ch_id)

    # Show distribution
    total_channels = len(channel_list)
    print(f"Total channels: {total_channels}")
    print(f"\nBank distribution:")

    for bank in sorted(banks.keys()):
        channels = banks[bank]
        count = len(channels)
        min_ch = min(channels)
        max_ch = max(channels)

        # Get actual depths from CSV
        min_electrode = min_ch + bank * gen.channels_per_bank
        max_electrode = max_ch + bank * gen.channels_per_bank
        min_electrode_info = gen.probe_loader.get_electrode_info(min_electrode)
        max_electrode_info = gen.probe_loader.get_electrode_info(max_electrode)
        min_depth = min_electrode_info['y'] / 1000  # in mm
        max_depth = max_electrode_info['y'] / 1000  # in mm

        print(f"  Bank {bank:2d}: {count:3d} channels (ch {min_ch:3d}-{max_ch:3d}), "
              f"elec {min_electrode:4d}-{max_electrode:4d}, "
              f"depth {min_depth:7.2f}-{max_depth:7.2f} mm")

    # Overall depth coverage
    all_channels = [ch_id for ch_id, _, _, _, _, _ in channel_list]
    depths = []
    for ch_id, bank, _, _, _, _ in channel_list:
        electrode = ch_id + bank * gen.channels_per_bank
        electrode_info = gen.probe_loader.get_electrode_info(electrode)
        depth = electrode_info['y'] / 1000  # in mm
        depths.append(depth)

    if depths:
        min_coverage = min(depths)
        max_coverage = max(depths)
        print(f"\nDepth coverage: {min_coverage:.2f} - {max_coverage:.2f} mm")
        print(f"Requested range: {depth_min_mm:.2f} - {depth_max_mm:.2f} mm")
        print(f"Coverage complete: {min_coverage <= depth_min_mm and max_coverage >= depth_max_mm}")

# Test 1: 0-20mm with even columns
print("\n\nTEST 1: Even columns, 0-20mm depth range")
print("Expected: Channels distributed across banks to cover 0-20mm")
gen = ImroGenerator('npx1.0-nhp')
channels = gen.create_channel_list_by_depth(
    depth_min_mm=0.0,
    depth_max_mm=20.0,
    column_selection='even',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)
analyze_channel_list(gen, channels, 0.0, 20.0)

# Test 2: 0-20mm with both columns
print("\n\nTEST 2: Both columns, 0-20mm depth range")
print("Expected: 384 channels distributed across banks to cover 0-20mm")
channels = gen.create_channel_list_by_depth(
    depth_min_mm=0.0,
    depth_max_mm=20.0,
    column_selection='both',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)
analyze_channel_list(gen, channels, 0.0, 20.0)

# Test 3: 0-44.16mm with even columns (full depth)
print("\n\nTEST 3: Even columns, 0-44.16mm depth range (full shank)")
print("Expected: All 192 even channels from banks 0-11")
channels = gen.create_channel_list_by_depth(
    depth_min_mm=0.0,
    depth_max_mm=44.16,
    column_selection='even',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)
analyze_channel_list(gen, channels, 0.0, 44.16)

# Test 4: 10-20mm with even columns (mid-range)
print("\n\nTEST 4: Even columns, 10-20mm depth range (mid-range)")
print("Expected: Channels from banks 1-2 that fall in 10-20mm")
channels = gen.create_channel_list_by_depth(
    depth_min_mm=10.0,
    depth_max_mm=20.0,
    column_selection='even',
    assignment_mode='striped',
    ap_gain=500,
    lf_gain=250,
    ap_filter=True,
    ref_type='external'
)
analyze_channel_list(gen, channels, 10.0, 20.0)

print("\n\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
