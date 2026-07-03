# Developer Guide — IMRO Generator

**For developers who want to extend or modify the IMRO generator.**

## Setup

```bash
# Clone or navigate to the repository
git clone <repo-url>
cd imro-generator

# Install in development mode
pip install -e .

# Install test dependencies
pip install pytest

# Run tests
pytest tests/
```

## Project Structure

```
imro_generator/
├── core/
│   └── imro_generator.py       # Core logic (channel allocation, I/O)
├── gui/
│   └── imro_config_gui.py      # PyQt5 GUI (visualization, user interaction)
└── __init__.py                  # Package entry point

tests/
├── test_depth_algorithm.py      # Algorithm validation
└── test_assignment_modes.py     # Mode testing

docs/
├── imro_algorithm.md            # Algorithm specification
├── imro_dev_guide_A_overview.md # Architecture overview
├── imro_dev_guide_B_howto.md    # How-to recipes
└── imro_user_guide_A_tutorial.md# User documentation
```

## Architecture

### Core Module (`imro_generator.py`)

Pure Python module with **no GUI dependencies**. Provides the `ImroGenerator` class:

**Constructor:**
- `ImroGenerator(probe_name)` — Load probe geometry from CSV

**Public methods:**
- `generate_electrode_list(depth_min_um, depth_max_um, assignment_mode)` — Generate electrode IDs for depth range
- `generate_imro_content(electrode_ids, ap_gain, lf_gain, ap_filter, ref_type)` — Convert electrode list to IMRO file format
- `parse_imro_file(imro_content)` — Parse IMRO file back to parameters and electrode list
- `parse_imro_header(header_line)` — Parse IMRO header line

**Attributes:**
- `df` — Pandas DataFrame with probe geometry (from channelmap.csv)
- `total_electrodes`, `total_channels`, `total_banks`, `max_depth` — Probe specifications
- `probe_mappings` — Bidirectional mapping of IMRO format names to probe types

### GUI Module (`imro_config_gui.py`)

PyQt5-based GUI that wraps `ImroGenerator`. Features:

- Interactive probe visualization (4416 electrode sites)
- Draggable depth range cursors (red = min, blue = max)
- Real-time electrode selection preview (green = selected)
- Menu-driven file operations (Load IMRO, Save IMRO, Save Kilosort Probe)
- Configuration settings: gains, filter, reference type, assignment mode
- Probe selection via menu

## Key Design Decisions

1. **Separation of concerns**: Core logic is GUI-independent; can be used in batch scripts or other UIs
2. **Instance methods**: `ImroGenerator` uses instance methods with DataFrame as source of truth (loaded from CSV)
3. **Type hints**: Fully typed for IDE support and static analysis
4. **CSV-based geometry**: Single authoritative source is channelmap.csv, loaded as Pandas DataFrame
5. **Flexible depth input**: GUI accepts any depth values; validation happens only on generation

## Testing

Run tests from the repository root:

```bash
pytest tests/ -v
```

Current test coverage:
- `test_depth_algorithm.py` — Validates channel selection across different depth ranges
- `test_assignment_modes.py` — Validates striped vs mixed bank assignment logic

## Common Tasks

### Add a new export format

1. Add static method to `ImroGenerator`:
   ```python
   @staticmethod
   def export_to_myformat(channel_list) -> dict:
       # implementation
   ```

2. Call from GUI or scripts:
   ```python
   config = ImroGenerator.export_to_myformat(self.current_channels)
   ```

### Add a GUI feature

1. Add method to `ImroConfigGUI` (e.g., `_create_xyz_widget()`)
2. Integrate into `_setup_ui()`
3. Connect signals to update logic

### Add a test

1. Create test function in `tests/test_*.py`:
   ```python
   def test_my_feature():
       result = ImroGenerator.some_method(...)
       assert result == expected
   ```

2. Run: `pytest tests/test_*.py::test_my_feature -v`

## Python Version

- **Minimum**: Python 3.8
- **Tested**: Python 3.9, 3.10, 3.11, 3.12
- **Required packages**: PyQt5 5.15+, pyqtgraph 0.12+, numpy 1.20+

## Dependencies

- **PyQt5** — GUI framework (Qt bindings)
- **pyqtgraph** — Advanced visualization (custom graphics items, plotting)
- **numpy** — Numerical operations for Kilosort export

## Performance Considerations

- Channel allocation uses randomized distribution for large depth ranges (intentional, for robustness)
- GUI visualization renders all 4416 electrodes as graphics items (acceptable for interactive use)
- IMRO file parsing uses regex (fast for single-line format)

## Building and Distribution

```bash
# Build distribution
python -m build

# Upload to PyPI (when ready)
twine upload dist/*
```

## Documentation

All user-facing documentation is in `docs/`:
- Build HTML: `cd docs && make html`
- Or read markdown directly

## Contributing

1. Create a branch: `git checkout -b feature/my-feature`
2. Write tests: Add test in `tests/`
3. Run tests: `pytest tests/ -v`
4. Update docs if needed
5. Commit: `git commit -m "Add feature: ..."`
6. Push and create PR

## Debugging

**Print debug info while running GUI:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Inspect channel allocation:**
```python
gen = ImroGenerator('npx1.0-nhp')
channels = gen.generate_electrode_list(0, 20000, 'mixed')
for i, electrode_id in enumerate(channels[:10]):
    print(f"Electrode {i}: {electrode_id}")
```

## Release Checklist

- [ ] Update version in `setup.py`
- [ ] Update `docs/` as needed
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Tag release: `git tag -a v0.2.0 -m "Release 0.2.0"`
- [ ] Build and upload: `python -m build && twine upload dist/*`
