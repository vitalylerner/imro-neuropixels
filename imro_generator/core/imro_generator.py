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
        probe_dir = Path(__file__).parent.parent / 'settings' / 'probes' / probe_name
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
        Assign channels to banks spanning a depth range and return the electrodes.

        Two assignment modes, which produce genuinely different physical layouts:

        - **mixed** — banks are mixed/interleaved throughout the range via
          round-robin: channel c is assigned bank ``b_start + (c % K)``. Both
          columns are recorded across the whole depth range, giving uniform
          two-column coverage. This is the sensible default for a wide range.

        - **striped** (single-column per depth region) — the two columns form
          separate stripes: even channels (column 0) fill the lower banks, odd
          channels (column 1) fill the upper banks. Each depth region is sampled
          by a single column, giving contiguous single-column coverage over a
          longer span. For a two-bank range this reproduces the layout of
          ``examples/single_column.imro`` (even → bank b_start, odd → bank
          b_start+1).

        Every channel is assigned to an in-range bank (see ``assign`` below); no
        channel is dropped or stranded on bank 0.

        Args:
            depth_min_um: Minimum depth in micrometers
            depth_max_um: Maximum depth in micrometers
            assignment_mode: 'mixed' (interleaved) or 'striped' (single-column)

        Returns:
            List of electrode IDs
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

        # Per-channel bank -> (electrode_id, depth) lookup, built once.
        by_channel = {}
        for r in self.df.itertuples():
            by_channel.setdefault(int(r.channel), {})[int(r.bank)] = (int(r.electrode), float(r.y))

        def in_range(y):
            return depth_min_um <= y <= depth_max_um

        def assign(channel_id, allowed_banks, preferred_bank):
            """Return an electrode for this channel, always in-range if possible.

            Preference order: the round-robin (preferred) bank if it is in range,
            otherwise the in-range allowed bank closest to it, otherwise the
            allowed bank whose depth is nearest the range. A channel is NEVER
            dropped, so no channel is ever stranded on bank 0 in the export.
            """
            cand = by_channel.get(channel_id, {})
            allowed = [b for b in allowed_banks if b in cand]
            if not allowed:
                allowed = sorted(cand.keys(), key=lambda b: abs(b - preferred_bank))
            in_r = sorted((b for b in allowed if in_range(cand[b][1])),
                          key=lambda b: (abs(b - preferred_bank), b))
            if in_r:
                return cand[in_r[0]][0]
            nearest = min(allowed, key=lambda b: min(abs(cand[b][1] - depth_min_um),
                                                     abs(cand[b][1] - depth_max_um)))
            return cand[nearest][0]

        selected_electrodes = []

        if assignment_mode == 'mixed':
            # Mixed: round-robin cycling through all K banks, interleaving both
            # columns uniformly across the depth range.
            all_banks = list(range(b_start, b_end + 1))
            for channel_id in range(self.total_channels):
                rr = b_start + (channel_id % k)
                selected_electrodes.append(assign(channel_id, all_banks, rr))

        else:  # striped mode: single-column-per-region
            # Split the K banks between the two columns: the lower ceil(K/2)
            # banks go to the even column (column 0), the upper floor(K/2) to the
            # odd column (column 1). Each column round-robins within its own bank
            # group. For K == 2 this gives even -> b_start, odd -> b_start + 1,
            # matching examples/single_column.imro; for K == 1 both columns share
            # the single bank.
            n_even_banks = (k + 1) // 2
            even_banks = [b_start + i for i in range(n_even_banks)]
            odd_banks = [b_start + i for i in range(n_even_banks, k)] or even_banks

            for i, channel_id in enumerate(range(0, self.total_channels, 2)):
                rr = even_banks[i % len(even_banks)]
                selected_electrodes.append(assign(channel_id, even_banks, rr))

            for i, channel_id in enumerate(range(1, self.total_channels, 2)):
                rr = odd_banks[i % len(odd_banks)]
                selected_electrodes.append(assign(channel_id, odd_banks, rr))

        return selected_electrodes

    def generate_imro_content(self, electrode_ids: List[int], ap_gain: int = 500,
                           lf_gain: int = 250, ap_filter: bool = True,
                           ref_type: str = 'tip', probe_type: int = 0) -> str:
        """
        Generate IMRO format content for selected electrodes.

        Produces the single-line, space-separated IMRO format that OpenEphys and
        SpikeGLX accept:

            (0,384)(0 0 1 500 250 1)(1 0 1 500 250 1)...(383 2 1 500 250 1)

        - Header is ``(probe_type,num_channels)`` with a NUMERIC probe type
          (0 = NP1.0). A non-numeric header such as ``NP1000`` is rejected by
          OpenEphys.
        - Every one of the ``num_channels`` channels gets exactly one entry.
          OpenEphys has no notion of a disabled channel: any channel not covered
          by ``electrode_ids`` is parked on bank 0 (its tip electrode).
        - Fields within an entry are SPACE-separated, not comma-separated.

        See ``docs/ISSUES.md`` for the history of this format (previous versions
        emitted a comma-separated, multi-line file with a ``NP1000`` header and
        fewer than ``num_channels`` entries, which OpenEphys silently rejected —
        falling back to its default map of all channels on the tip).

        Args:
            electrode_ids: List of selected electrode IDs
            ap_gain: AP band gain (50-3000, typically 500)
            lf_gain: LF band gain (50-3000, typically 250)
            ap_filter: Whether AP highpass filter is ON
            ref_type: Reference type ('external', 'tip', or 'on_shank')
            probe_type: Numeric IMRO probe type for the header (0 = NP1.0)

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

        filter_flag = 1 if ap_filter else 0

        # Map each selected electrode to its channel/bank. If two selected
        # electrodes share a channel (should not happen for a valid selection),
        # the lowest bank wins.
        selected_set = set(electrode_ids)
        channel_bank = {}
        for _, row in self.df[self.df['electrode'].isin(selected_set)].iterrows():
            channel_id = int(row['channel'])
            bank = int(row['bank'])
            if channel_id not in channel_bank or bank < channel_bank[channel_id]:
                channel_bank[channel_id] = bank

        # Emit an entry for EVERY channel; uncovered channels default to bank 0.
        # No trailing newline: OpenEphys-exported files are a single line with no
        # terminator, and matching that exactly avoids parser rejection.
        parts = [f"({probe_type},{self.total_channels})"]
        for channel_id in range(self.total_channels):
            bank = channel_bank.get(channel_id, 0)
            parts.append(f"({channel_id} {bank} {ref_id} {ap_gain} {lf_gain} {filter_flag})")

        return "".join(parts)

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

            # Find electrode for this channel-bank pair. Reference sites are
            # included (see _get_electrode_in_bank) so a full-bank file round-trips.
            row = self.df[
                (self.df['channel'] == channel_id) &
                (self.df['bank'] == bank)
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
        Infer whether entries use mixed (interleaved) or striped (single-column).

        - striped (single-column): the even column occupies a contiguous lower
          bank block and the odd column a contiguous upper block, so every even
          channel's bank is below every odd channel's bank
          (``max(even) < min(odd)``).
        - mixed (interleaved): round-robin makes the columns share/interleave the
          banks, so the even column also reaches the higher banks
          (``max(even) >= min(odd)``).

        For a single- or two-bank range the two modes coincide; the ordered-
        disjoint test reports 'striped' there, but the two produce identical maps.
        """
        even_banks = [e['bank'] for e in entries if e['channel'] % 2 == 0]
        odd_banks = [e['bank'] for e in entries if e['channel'] % 2 == 1]
        if not even_banks or not odd_banks:
            return 'mixed'

        if max(even_banks) < min(odd_banks):
            return 'striped'
        return 'mixed'

    def _get_electrode_in_bank(self, channel_id: int, bank: int, depth_min_um: int, depth_max_um: int) -> int:
        """Find electrode for channel in bank, return if in depth range, else None.

        Reference sites are NOT excluded: on this probe channel 191 is a reference
        in every bank, but OpenEphys still assigns it to the selected bank like any
        other channel. Dropping it here would make a "full bank" configuration
        impossible (channel 191 would fall back to bank 0).
        """
        row = self.df[
            (self.df['channel'] == channel_id) &
            (self.df['bank'] == bank)
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
        mappings_path = Path(__file__).parent.parent / 'settings' / 'probes' / 'probes.csv'

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

