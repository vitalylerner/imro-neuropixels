# Documentation Audit Report

## Critical Mismatches

### 1. **Column Selection (Even/Odd/Both)**
**Documentation claims:**
- QUICKSTART.md (lines 30-32): "Choose your electrodes... Select **Even**, **Odd**, or **Both** columns"
- imro_user_guide_A_tutorial.md (lines 49-52): "Choose your **column selection**... Even columns only, Odd columns only, Both columns"

**Actual code:**
- GUI removed these controls entirely
- Only has: Depth Range + Assignment Mode (Striped/Mixed)
- No column selection UI exists

**Status:** ❌ NEEDS FIX - Remove column selection references from docs OR restore controls to GUI

---

### 2. **Button Labels**
**Documentation claims:**
- imro_user_guide_A_tutorial.md (line 94): "Click **Generate IMRO**"

**Actual code:**
- GUI has button labeled: "Generate Channels" (imro_config_gui.py:284)

**Status:** ❌ NEEDS FIX - Update docs to say "Generate Channels"

---

### 3. **Save Functionality**
**Documentation claims:**
- QUICKSTART.md (line 42): "Click **Save As** to save an IMRO file"

**Actual code:**
- No "Save As" button in UI
- Menu → Map → "Save IMRO" (imro_config_gui.py:126-127)

**Status:** ❌ NEEDS FIX - Change docs to reference "Map → Save IMRO"

---

### 4. **Load Functionality**  
**Documentation claims:**
- QUICKSTART.md (line 47): "Click **Load** to open a saved IMRO file"
- imro_user_guide_A_tutorial.md (line 155): "Click **Load IMRO**"

**Actual code:**
- Menu → Map → "Load IMRO" (imro_config_gui.py:122-123)

**Status:** ⚠️ PARTIALLY OK - Docs are correct about "Load IMRO" but don't mention it's in a menu

---

### 5. **Reference Type Settings**
**Documentation claims:**
- imro_user_guide_A_tutorial.md (lines 82-90): Describes External vs Tip reference with "Own bank" / "Same reference" options

**Actual code:**
- GUI shows Reference radio buttons (External / Tip) on lines 193-200
- BUT ref_mode_container (Own bank / Same reference) is HIDDEN: line 228 `setVisible(False)`
- These controls are never shown to users

**Status:** ❌ NEEDS FIX - Either show the ref_mode controls OR remove them from docs

---

### 6. **IMRO Format Header**
**Documentation claims:**
- README.md (line 39): "Generate IMRO format content"
- imro_user_guide_A_tutorial.md: Mentions probe type 0 (NP1000)

**Actual code:**
- generate_imro_content() (imro_generator.py:148): Hardcodes "(NP1000,384)"
- Does NOT use actual probe type from probe.json
- Does NOT use probe_mappings that were loaded (lines 36-37)

**Status:** ⚠️ WORKS BUT INCOMPLETE - Code loads probe mappings but doesn't use them

---

### 7. **Assignment Mode Descriptions**
**Documentation claims:**
- imro_user_guide_A_tutorial.md (lines 66-72):
  - "Striped mode (default): Channels 0, K, 2K, ... → Bank 0; channels 1, K+1, 2K+1, ... → Bank 1"
  - "Mixed mode (for 'both' columns): Pairs (0,1), (2,3), (4,5), ... assigned to the same bank"

**Actual code:**
- Default is MIXED (line 277: `self.assignment_mixed_radio.setChecked(True)`)
- Striped implementation matches description (lines 85-91)
- Mixed implementation uses even/odd column interleaving, NOT pairs as described (lines 98-116)

**Status:** ❌ NEEDS FIX - Default should be Striped OR update docs to say Mixed is default

---

### 8. **Kilosort Export**
**Documentation claims:**
- QUICKSTART.md (line 44): "Can also export Kilosort probe files (.json)"
- README.md (line 12): "Export Kilosort4-compatible probe configurations"

**Actual code:**
- Menu → Map → "Save Kilosort Probe" exists (line 130)
- Function exists: save_kilosort_probe() - implementation not checked

**Status:** ⚠️ UNTESTED - Feature exists but need to verify it works correctly

---

### 9. **Probe Selection**
**Documentation claims:**
- Not clearly documented in user guides

**Actual code:**
- GUI has Probe → Change Probe menu (lines 106-117)
- Only hardcoded to 'npx1.0-nhp' at startup (line 36)
- Menu allows switching probes

**Status:** ⚠️ UNDOCUMENTED - User docs don't mention probe selection feature

---

### 10. **Depth Range Input**
**Documentation claims:**
- QUICKSTART.md (lines 26-27): "Drag the red (min) and blue (max) cursor lines on the right"
- imro_user_guide_A_tutorial.md: Describes entering depth in mm

**Actual code:**
- ✓ Correctly allows typing in spinboxes (spinboxes have range -999999 to 999999)
- ✓ Correctly allows dragging cursors (cursor handlers no longer clamp)

**Status:** ✓ OK - Documentation matches implementation

---

## Summary

**Critical Issues (Block Publishing):**
1. Column selection (Even/Odd/Both) - major feature documented but not in GUI
2. Reference mode controls - UI exists but hidden, docs describe it as available
3. Assignment mode default - docs say striped, code uses mixed
4. Button labels - docs reference "Generate IMRO" and "Save As" which don't match UI

**Minor Issues:**
- Mixed mode algorithm description doesn't match implementation
- Probe mapping loaded but not used
- Probe selection not documented

## Recommendations

**Before publishing, MUST:**
1. Decide: Keep column selection in docs and restore to GUI, OR remove from docs entirely
2. Update all button label references in docs to match actual UI
3. Fix reference mode: either show controls or remove from docs
4. Fix default assignment mode: change code to striped OR update docs
5. Update menu paths in docs (Load/Save are in Menu → Map)

**Should update (less critical):**
6. Document Probe → Change Probe feature
7. Update mixed mode description to match actual even/odd column interleaving
8. Verify Kilosort export works correctly
