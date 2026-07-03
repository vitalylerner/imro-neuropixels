"""Test assignment mode options for IMRO channel generation."""

from imro_generator.core.imro_generator import ImroGenerator


def test_striped_mode():
    """Test striped mode: even banks get even channels (when K is even)."""
    print("Testing STRIPED mode (0-20mm, both columns):")
    gen = ImroGenerator('npx1.0-nhp')
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

    print(f"Total channels: {len(channels)}")

    # Analyze bank assignments for even and odd channels
    even_banks = {}
    odd_banks = {}

    for ch_id, bank, ref_id, ap_gain, lf_gain, ap_filter in channels:
        if ch_id % 2 == 0:
            even_banks[ch_id] = bank
        else:
            odd_banks[ch_id] = bank

    # Show first few assignments
    print("\nFirst 10 even channels:")
    for ch_id in sorted(even_banks.keys())[:10]:
        print(f"  Channel {ch_id} -> Bank {even_banks[ch_id]}")

    print("\nFirst 10 odd channels:")
    for ch_id in sorted(odd_banks.keys())[:10]:
        print(f"  Channel {ch_id} -> Bank {odd_banks[ch_id]}")

    # Check channels 0 and 1
    bank_0 = even_banks.get(0, None)
    bank_1 = odd_banks.get(1, None)
    print(f"\nChannel 0 -> Bank {bank_0}, Channel 1 -> Bank {bank_1}")
    print(f"Same bank? {bank_0 == bank_1}")
    print()


def test_mixed_mode():
    """Test mixed mode: consecutive even-odd pairs share same bank."""
    print("Testing MIXED mode (0-20mm, both columns):")
    gen = ImroGenerator('npx1.0-nhp')
    channels = gen.create_channel_list_by_depth(
        depth_min_mm=0.0,
        depth_max_mm=20.0,
        column_selection='both',
        assignment_mode='mixed',
        ap_gain=500,
        lf_gain=250,
        ap_filter=True,
        ref_type='external'
    )

    print(f"Total channels: {len(channels)}")

    # Analyze bank assignments for even and odd channels
    even_banks = {}
    odd_banks = {}

    for ch_id, bank, ref_id, ap_gain, lf_gain, ap_filter in channels:
        if ch_id % 2 == 0:
            even_banks[ch_id] = bank
        else:
            odd_banks[ch_id] = bank

    # Show first few assignments
    print("\nFirst 10 even channels:")
    for ch_id in sorted(even_banks.keys())[:10]:
        print(f"  Channel {ch_id} -> Bank {even_banks[ch_id]}")

    print("\nFirst 10 odd channels:")
    for ch_id in sorted(odd_banks.keys())[:10]:
        print(f"  Channel {ch_id} -> Bank {odd_banks[ch_id]}")

    # Check channels 0 and 1
    bank_0 = even_banks.get(0, None)
    bank_1 = odd_banks.get(1, None)
    print(f"\nChannel 0 -> Bank {bank_0}, Channel 1 -> Bank {bank_1}")
    print(f"Same bank? {bank_0 == bank_1}")
    print()


def test_extract_mode():
    """Test that extract_config_from_channels correctly infers assignment mode."""
    print("Testing mode inference from channel list:")
    gen = ImroGenerator('npx1.0-nhp')

    # Generate striped
    striped_channels = gen.create_channel_list_by_depth(
        depth_min_mm=0.0,
        depth_max_mm=20.0,
        column_selection='both',
        assignment_mode='striped',
        ap_gain=500,
        lf_gain=250,
        ap_filter=True,
        ref_type='external'
    )

    cfg_striped = gen.extract_config_from_channels(striped_channels)
    print(f"Striped config -> assignment_mode: {cfg_striped.get('assignment_mode')}")

    # Generate mixed
    mixed_channels = gen.create_channel_list_by_depth(
        depth_min_mm=0.0,
        depth_max_mm=20.0,
        column_selection='both',
        assignment_mode='mixed',
        ap_gain=500,
        lf_gain=250,
        ap_filter=True,
        ref_type='external'
    )

    cfg_mixed = gen.extract_config_from_channels(mixed_channels)
    print(f"Mixed config -> assignment_mode: {cfg_mixed.get('assignment_mode')}")
    print()


if __name__ == '__main__':
    test_striped_mode()
    test_mixed_mode()
    test_extract_mode()
