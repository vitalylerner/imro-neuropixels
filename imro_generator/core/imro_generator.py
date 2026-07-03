import pandas as pd
from pathlib import Path
from typing import List
import random


class ImroGenerator:
    """Load probe geometry from CSV and generate electrode lists."""

    def __init__(self, probe_name: str = 'npx1.0-nhp'):
        """
        Initialize ImroGenerator with a probe.

        Args:
            probe_name: Name of probe (default: 'npx1.0-nhp')
        """
        # Construct path to probe CSV
        probe_dir = Path(__file__).parent.parent.parent / 'settings' / 'probes' / probe_name
        csv_path = probe_dir / 'channelmap.csv'

        if not csv_path.exists():
            raise FileNotFoundError(f"Channel map not found: {csv_path}")

        # Load CSV as pandas DataFrame
        self.df = pd.read_csv(csv_path)

        # Convert ref column to boolean
        self.df['ref'] = self.df['ref'].astype(bool)

        # Derive probe specifications
        self.total_electrodes = len(self.df)
        self.total_channels = int(self.df['channel'].max()) + 1
        self.total_banks = int(self.df['bank'].max()) + 1
        self.max_depth = int(self.df['y'].max())

        # Load probe mappings
        self.probe_mappings = self._load_probe_mappings()

    def generate_electrode_list(self, depth_min_um: int, depth_max_um: int, assignment_mode: str = 'mixed') -> List[int]:
        """
        Interleaved assignment algorithm for electrode selection.

        Assigns channels round-robin across K banks spanning the depth range,
        creating near-optimal uniform distribution of electrodes.

        Algorithm:
        1. Find banks that cover the depth range (B_start, B_end)
        2. Calculate K = number of banks needed
        3. For striped mode: assign all channels sequentially through banks
           For mixed mode: shuffle channels, run algorithm, then map back
        4. Filter channels where electrode depth falls in [depth_min_um, depth_max_um]

        Args:
            depth_min_um: Minimum depth in micrometers
            depth_max_um: Maximum depth in micrometers
            assignment_mode: 'striped' or 'mixed'

        Returns:
            List of electrode IDs in depth order
        """
        # Find banks that cover this range
        b_start = None
        b_end = None

        for bank in range(self.total_banks):
            bank_data = self.df[self.df['bank'] == bank]
            if len(bank_data) == 0:
                continue

            bank_min_um = float(bank_data['y'].min())
            bank_max_um = float(bank_data['y'].max())

            if b_start is None and depth_min_um <= bank_max_um:
                b_start = bank

            if depth_max_um >= bank_min_um:
                b_end = bank

        if b_start is None or b_end is None:
            return []

        k = b_end - b_start + 1
        selected_electrodes = []

        if assignment_mode == 'striped':
            # Striped: sequential cycling through banks (round-robin)
            for channel_id in range(self.total_channels):
                assigned_bank = b_start + (channel_id % k)
                electrode = self._get_electrode_in_bank(channel_id, assigned_bank, depth_min_um, depth_max_um)
                if electrode is not None:
                    selected_electrodes.append(electrode)

        else:  # mixed mode
            # Mixed: interleave columns deterministically for balanced distribution
            # Process channels as: 0, 1, 2, 3, 4, 5, ... (mixing even/odd)
            # but traverse with different pattern than striped
            # Use offset to create different bank assignments
            even_channels = list(range(0, self.total_channels, 2))  # 0, 2, 4, ...
            odd_channels = list(range(1, self.total_channels, 2))   # 1, 3, 5, ...

            # Interleave: process even and odd channels together
            for i in range(len(even_channels)):
                # Even channel
                channel_id = even_channels[i]
                assigned_bank = b_start + (i % k)
                electrode = self._get_electrode_in_bank(channel_id, assigned_bank, depth_min_um, depth_max_um)
                if electrode is not None:
                    selected_electrodes.append(electrode)

                # Odd channel
                if i < len(odd_channels):
                    channel_id = odd_channels[i]
                    assigned_bank = b_start + ((i + k//2) % k) if k > 1 else b_start
                    electrode = self._get_electrode_in_bank(channel_id, assigned_bank, depth_min_um, depth_max_um)
                    if electrode is not None:
                        selected_electrodes.append(electrode)

        return selected_electrodes

    def generate_imro_content(self, electrode_ids: List[int], ap_gain: int = 500,
                           lf_gain: int = 250, ap_filter: bool = True,
                           ref_type: str = 'tip') -> str:
        """
        Generate IMRO format content for selected electrodes.

        Args:
            electrode_ids: List of selected electrode IDs
            ap_gain: AP band gain (50-3000, typically 500)
            lf_gain: LF band gain (50-3000, typically 250)
            ap_filter: Whether AP highpass filter is ON
            ref_type: Reference type ('external', 'tip', or 'on_shank')

        Returns:
            IMRO format string ready to write to file
        """
        # Determine reference ID based on type
        if ref_type == 'external':
            ref_id = 0
        elif ref_type == 'tip':
            ref_id = 1
        else:  # on_shank
            ref_id = 2

        # Create mapping of selected electrodes
        selected_set = set(electrode_ids)

        # Build IMRO entries for all 384 channels
        imro_lines = ["(NP1000,384)"]

        for channel_id in range(self.total_channels):
            # Find which electrode (if any) is assigned to this channel
            matching_rows = self.df[
                (self.df['channel'] == channel_id) &
                (self.df['electrode'].isin(selected_set))
            ]

            if len(matching_rows) > 0:
                # Use first matching electrode for this channel
                row = matching_rows.iloc[0]
                bank = int(row['bank'])
                filter_flag = 1 if ap_filter else 0

                imro_entry = f"({channel_id},{bank},{ref_id},{ap_gain},{lf_gain},{filter_flag})"
                imro_lines.append(imro_entry)

        return "\n".join(imro_lines) + "\n"

    def parse_imro_file(self, imro_content: str) -> dict:
        """
        Parse IMRO format and extract selected electrodes and settings.

        Handles both formats:
        - Multi-line: header on line 1, entries on separate lines
        - Single-line: header and entries all on one line

        Entries can be:
        - Comma-separated: (ChannelID,Bank,Reference,APgain,LFgain,Filter)
        - Space-separated: (ChannelID Bank Reference APgain LFgain Filter)

        Args:
            imro_content: IMRO file content as string

        Returns:
            Dictionary with electrode info and inferred settings
        """
        import re

        # Clean up the content
        content = imro_content.strip()

        # Find header: first match of (something,number)
        header_match = re.match(r'\(([^,)]+),(\d+)\)', content)
        if not header_match:
            raise ValueError(f"Invalid IMRO format: could not parse header")

        identifier = header_match.group(1)
        num_channels = int(header_match.group(2))

        # Find all entries: (values)
        # Entries can contain spaces or commas
        entry_pattern = r'\(([^)]+)\)'
        entries_text = re.findall(entry_pattern, content)

        if not entries_text:
            raise ValueError("No entries found in IMRO file")

        # Skip header (first match)
        entries_text = entries_text[1:]

        # Parse entries
        entries = []
        ap_gain = None
        lf_gain = None
        ap_filter = None

        for entry_text in entries_text:
            # Try parsing as space-separated first, then comma-separated
            if ' ' in entry_text:
                parts = entry_text.split()
            else:
                parts = entry_text.split(',')

            if len(parts) != 6:
                continue

            try:
                channel_id = int(parts[0])
                bank = int(parts[1])
                ref_id = int(parts[2])
                ap_gain = int(parts[3])
                lf_gain = int(parts[4])
                ap_filter = bool(int(parts[5]))

                entries.append({
                    'channel': channel_id,
                    'bank': bank,
                    'reference': ref_id,
                    'ap_gain': ap_gain,
                    'lf_gain': lf_gain,
                    'ap_filter': ap_filter
                })
            except (ValueError, IndexError):
                continue

        if not entries:
            raise ValueError("Could not parse any valid entries from IMRO file")

        # Extract electrode IDs from channel-bank pairs
        electrode_ids = []
        depths = []

        for entry in entries:
            channel_id = entry['channel']
            bank = entry['bank']

            # Find electrode for this channel-bank pair
            row = self.df[
                (self.df['channel'] == channel_id) &
                (self.df['bank'] == bank) &
                (self.df['ref'] == False)
            ]

            if len(row) > 0:
                electrode_id = int(row.iloc[0]['electrode'])
                depth_um = float(row.iloc[0]['y'])
                electrode_ids.append(electrode_id)
                depths.append(depth_um)

        depths.sort()
        depth_min_um = int(depths[0]) if depths else 0
        depth_max_um = int(depths[-1]) if depths else 0

        # Infer assignment mode by analyzing channel-bank pattern
        assignment_mode = self._infer_assignment_mode(entries)

        return {
            'electrode_ids': electrode_ids,
            'depths_um': sorted(depths),
            'depth_min_um': depth_min_um,
            'depth_max_um': depth_max_um,
            'ap_gain': ap_gain or 500,
            'lf_gain': lf_gain or 250,
            'ap_filter': ap_filter if ap_filter is not None else True,
            'assignment_mode': assignment_mode,
            'probe_identifier': identifier,
            'num_channels': num_channels
        }

    def _infer_assignment_mode(self, entries: list) -> str:
        """
        Infer whether entries use striped or mixed assignment.

        Striped: channels 0,1,2,3,... assigned to banks 0,1,2,0,1,2,...
        Mixed: even channels vs odd channels get different offsets
        """
        if len(entries) < 10:
            return 'striped'

        # Check pattern of first 10 channels
        striped_score = 0
        mixed_score = 0

        for i in range(min(10, len(entries))):
            entry = entries[i]
            channel = entry['channel']
            bank = entry['bank']
            k = 3  # Assume 3 banks for inference

            # Check striped pattern: bank = (channel % k)
            expected_bank_striped = channel % k
            if bank == expected_bank_striped:
                striped_score += 1

            # Check mixed pattern: even and odd channels have different patterns
            if channel % 2 == 0:
                expected_bank_mixed = (channel // 2) % k
            else:
                expected_bank_mixed = ((channel - 1) // 2 + k // 2) % k
            if bank == expected_bank_mixed:
                mixed_score += 1

        return 'mixed' if mixed_score > striped_score else 'striped'

    def _get_electrode_in_bank(self, channel_id: int, bank: int, depth_min_um: int, depth_max_um: int) -> int:
        """Find electrode for channel in bank, return if in depth range, else None."""
        row = self.df[
            (self.df['channel'] == channel_id) &
            (self.df['bank'] == bank) &
            (self.df['ref'] == False)
        ]

        if len(row) > 0:
            electrode_id = int(row.iloc[0]['electrode'])
            depth_um = float(row.iloc[0]['y'])

            if depth_min_um <= depth_um <= depth_max_um:
                return electrode_id

        return None

    def _load_probe_mappings(self) -> dict:
        """Load probe type to IMRO format mappings from probes.csv.

        Returns dict with:
        - 'format_to_types': maps IMRO format name to list of probe types
        - 'type_to_format': maps probe type number to IMRO format name
        """
        mappings_path = Path(__file__).parent.parent.parent / 'settings' / 'probes' / 'probes.csv'

        if not mappings_path.exists():
            return {'format_to_types': {}, 'type_to_format': {}}

        try:
            mappings_df = pd.read_csv(mappings_path)
            format_to_types = {}
            type_to_format = {}

            for _, row in mappings_df.iterrows():
                imro_format = row['imro_format']
                probe_type = int(row['probe_type'])
                part_numbers = row['part_numbers']

                # Build format -> types mapping
                if imro_format not in format_to_types:
                    format_to_types[imro_format] = []
                format_to_types[imro_format].append(probe_type)

                # Build type -> format mapping
                type_to_format[probe_type] = imro_format

            return {
                'format_to_types': format_to_types,
                'type_to_format': type_to_format
            }
        except Exception as e:
            print(f"Warning: Could not load probe mappings: {e}")
            return {'format_to_types': {}, 'type_to_format': {}}

    def parse_imro_header(self, header_line: str) -> tuple:
        """
        Parse IMRO header which can be either:
        - (NP1000,384) - text format name
        - (0,384) - numeric probe type
        - (1020,384) - numeric probe type

        Returns:
            (format_name_or_type, num_channels)
        """
        # Remove parentheses and split
        content = header_line.strip('()')
        parts = content.split(',')

        if len(parts) != 2:
            raise ValueError(f"Invalid IMRO header format: {header_line}")

        identifier = parts[0].strip()
        num_channels = int(parts[1])

        return identifier, num_channels

    def generate_kilosort_probe(self, electrode_ids: List[int]) -> dict:
        """
        Generate Kilosort4 probe dictionary from selected electrodes.

        Args:
            electrode_ids: List of electrode IDs to include

        Returns:
            Dictionary with keys: chanMap, xc, yc, kcoords, n_chan
            All values are lists compatible with JSON serialization
        """
        selected_set = set(electrode_ids)

        chanMap = []
        xc = []
        yc = []
        kcoords = []

        for _, row in self.df.iterrows():
            electrode_id = int(row['electrode'])
            if electrode_id in selected_set:
                channel = int(row['channel'])
                x = float(row['x'])
                y = float(row['y'])
                bank = int(row['bank'])

                chanMap.append(channel)
                xc.append(x)
                yc.append(y)
                kcoords.append(bank)

        return {
            'chanMap': chanMap,
            'xc': xc,
            'yc': yc,
            'kcoords': kcoords,
            'n_chan': len(chanMap)
        }

