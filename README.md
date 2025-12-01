# Rhino Object Naming Toolkit

A lightweight RhinoPython toolkit for inspecting, analyzing, and automatically renaming Rhino object names to remove duplicate names.  


---

## Running the Toolkit

### One-off run (from Rhino command line)

Run this in the Rhino command prompt:

```
_-RunPythonScript "FULL_PATH_TO/toolkit.py"
```

**macOS example:**

```
_-RunPythonScript "/Users/UserName/Desktop/RhinoScripts/toolkit.py"
```

**Windows example:**

```
_-RunPythonScript "C:\Users\UserName\Documents\RhinoScripts\toolkit.py"
```

This launches the interactive Toolkit menu.

---

## Adding a Toolbar Button (Recommended)

1. Open Rhino toolbar editor:  
   - **Windows:** Tools → Toolbar Layout…  
   - **macOS:** Rhino → Preferences → Toolbars  
2. Choose (or create) a toolbar.  
3. Right-click → **New Button…**  
4. In the **Command** field, enter:

```
! _-RunPythonScript "FULL_PATH_TO/toolkit.py"
```

5. Add an optional tooltip and icon.

One click now runs your Toolkit.

---

## Toolkit Menu Behavior

When `toolkit.py` runs, it enters a persistent loop:

```
Choose action (Selected only: OFF)
Options: SelectedObjects, NameStats, ListNames, RenameDry, RenameApply, Exit
```

---

# Actions

## SelectedObjects

Toggles selected-only mode.

- **OFF** → operate on all model-space objects  
- **ON** → operate on only selected objects  

If ON and nothing is selected, the Toolkit warns the user.

---

## NameStats

```
view_object_names.get_object_name_stats(
    include_hidden=True,
    selected_only=selected_only
)
```

Outputs:

- Total objects  
- Distinct names  
- Duplicate name groups  
- Duplicate instance count  
- Per-name duplicate frequencies  

---

## ListNames

```
view_object_names.list_object_info(
    include_hidden=True,
    include_description=True,
    selected_only=selected_only
)
```

Outputs:

- Object name  
- Description (if present)  
- Marks duplicates as **DUPLICATE**

---

## RenameDry

Simulates renaming actions **without** modifying the document:

```
rename_objects.rename_objects_unique(
    include_hidden=True,
    dry_run=True,
    selected_only=selected_only
)
```

Shows exactly what *would* be renamed.

---

## RenameApply

Performs real renaming to enforce unique naming:

```
rename_objects.rename_objects_unique(
    include_hidden=True,
    dry_run=False,
    selected_only=selected_only
)
```

Example output:

```
Renamed: 'Box' -> 'Box 001'
```

---

## Exit

Leaves the Toolkit loop.

---

# How Object Filtering Works

## Selected-only Mode

If `selected_only=True`, the system uses:

```
rs.SelectedObjects()
```

as the working set.

---

## Normal Mode (Model Space Only)

If `selected_only=False`, the system uses:

```
get_model_space_objects(...)
```

This filters out:

- Layout / page-space objects  
- Hidden / locked objects (optional)  
- Lights  
- Grips  

It keeps only true **model-space geometry**.

---

# Renaming Strategy

`rename_objects.rename_objects_unique(...)` performs:

1. Collect object IDs  
2. Optional filters (unnamed, hidden, locked)  
3. Count name occurrences  
4. Identify duplicates  
5. Sort objects by `(name, guid)` for deterministic renaming  
6. For each duplicate group:  
   - Keep one unmodified base name  
   - Assign suffixes (e.g., `" {num:03d}"`) to the rest:

```
Box
Box 001
Box 002
```

7. Ensure uniqueness using `ObjectsByName`  
8. Print actions (dry-run or real)

### Returns:

- Number of renamed objects  
- Final name frequency dictionary  

### Suffix formats:

- `" {num:03d}"` → `Name 001`  
- `"-{num:03d}"` → `Name-001`  
- `".{num}"` → `Name.1`  

---

# Customization

## In `view_object_names.py`

```
include_unnamed = True
include_hidden = True
include_description = True
```

## In `rename_objects.py`

```
suffix_fmt = " {num:03d}"
include_unnamed = True
include_hidden = True
```

## In `utils.py`

```
include_hidden = True
include_locked = True
include_grips = False
include_lights = False
```

Modify these defaults to match your workflow.

---

# Recommended Folder Structure

```
RhinoToolkit/
│
├── toolkit.py
├── rename_objects.py
├── view_object_names.py
├── utils.py
│
└── README.md
```

---

# License

MIT License
