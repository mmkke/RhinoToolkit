
"""
Utilities for managing and enforcing unique object names in a Rhino document.

This module provides helper functions for detecting naming conflicts and
renaming Rhino objects in a deterministic, non-destructive manner. Its primary
use case is maintaining clean and consistent naming conventions in complex
Rhino models, especially when objects are duplicated, imported, or generated
by scripts.

Main features
-------------
- Detect whether a name is already in use (`name_in_use`)
- Generate the next available unique name using a configurable suffix pattern
  (`next_unique_name`)
- Rename objects so that all names within the working set are unique
  (`rename_objects_unique`)

Supported workflows
-------------------
Object renaming can operate on:
- All model-space objects (default)
- Only the currently selected objects (`selected_only=True`)
- Named or unnamed objects, depending on filtering parameters
- Hidden or locked objects, if allowed by parameters

The renaming procedure is deterministic:
objects are sorted by `(name, GUID)` so repeated runs yield consistent results.

This module is intended to be called from interactive tooling such as
`toolbox.py`, but each function can also be used independently.
"""

import rhinoscriptsyntax as rs
from utils import get_model_space_objects


def name_in_use(name):
    """Return True if any object in the document already uses 'name'."""
    objs = rs.ObjectsByName(name)
    return bool(objs)


def next_unique_name(base, suffix_fmt, start_at=2):
    """
    Return a unique object name by appending an incrementing numeric suffix.
    
    Parameters
    ----------
    base : str
        Base name to modify.
    suffix_fmt : str
        A Python format string, e.g. " {num:03d}".
    start_at : int
        Initial numeric suffix to try.
    """
    base = base or "Object"

    if not name_in_use(base):
        return base

    n = start_at
    while True:
        candidate = "{}{}".format(base, suffix_fmt.format(num=n))
        if not name_in_use(candidate):
            return candidate
        n += 1


def rename_objects_unique(selected_only=False, include_unnamed=True, include_hidden=True, dry_run=False, suffix_fmt=" {num:03d}"):
    """
    Rename all Rhino objects so that each named object has a unique name.
    Reports statistics before renaming.

    Parameters
    ----------
    selected_only : bool
        Whether to only use selected objects.
    include_unnamed : bool
        Whether to include unnamed objects objects.
    include_hidden : bool
        Whether to include hidden or locked objects.
    dry_run : bool
        If True, only report renaming actions.
    suffix_fmt : str
        Formatting for numeric suffix, e.g. " {num:03d}" or "-{num:03d}".

    Returns
    -------
    renamed_count : int
        Number of renamed objects.

    stats : dict
        Statistics about names and duplicates.
    """

    # ------------------------------------------------------------
    # Collect object IDs
    # ------------------------------------------------------------
    if selected_only:
        ids = rs.SelectedObjects()
    else:
        ids = get_model_space_objects(include_hidden=True,
                                include_locked=True,
                                include_grips=False,
                                include_lights=False)
    if not ids:
        print("No objects found.")
        return 0, {}

    # Filter out unnamed objects
    if not include_unnamed:
        ids = [obj_id for obj_id in ids if (rs.ObjectName(obj_id) or "").strip()]

    if not include_hidden:
        ids = [obj_id for obj_id in ids
               if not rs.IsHidden(obj_id) and not rs.IsObjectLocked(obj_id)]

    if not ids:
        print("No named objects found.")
        return 0, {}

    # ------------------------------------------------------------
    # Count frequencies of each name
    # ------------------------------------------------------------
    name_counts = {}
    for obj_id in ids:
        nm = rs.ObjectName(obj_id) or "Object"
        name_counts[nm] = name_counts.get(nm, 0) + 1

    # Detect duplicates
    dup_names = dict((n, c) for (n, c) in name_counts.items() if c > 1)

    # ------------------------------------------------------------
    # Print statistics
    # ------------------------------------------------------------
    print("----- Object Name Statistics -----")
    print("Total named objects:", len(ids))
    print("Distinct names:", len(name_counts))
    print("Duplicate name groups:", len(dup_names))
    print("Total duplicate instances:", sum(dup_names.values()))
    print("")

    # print("All name frequencies:")
    # for nm, c in sorted(name_counts.items()):
    #     print("  Name:", nm, " Count:", c)
    # print("")

    if dup_names:
        print("Duplicate name frequencies:")
        for nm, c in sorted(dup_names.items()):
            print("  Name:", nm, " Count:", c)
        print("")
    else:
        print("No duplicates detected.")
        print("")

    # ------------------------------------------------------------
    # If no duplicates at all, nothing to rename
    # ------------------------------------------------------------
    if not dup_names:
        print("All object names are already unique.")
        return 0, name_counts

    # ------------------------------------------------------------
    # Prepare for renaming
    # ------------------------------------------------------------
    renamed = 0
    assigned_base_once = set()

    # Sort by (name, guid-string) for deterministic behavior
    ids_sorted = sorted(ids, key=lambda i: ((rs.ObjectName(i) or ""), str(i)))

    # ------------------------------------------------------------
    # Rename algorithm
    # ------------------------------------------------------------
    print("----- Renaming Duplicates -----")
    for obj_id in ids_sorted:
        base = rs.ObjectName(obj_id) or "Object"

        if base not in dup_names:
            continue

        if base not in assigned_base_once:
            # Try to use base name first
            if not name_in_use(base):
                new_name = base
            else:
                new_name = next_unique_name(base, suffix_fmt, start_at=1)
            assigned_base_once.add(base)
        else:
            # Later duplicates get suffix
            new_name = next_unique_name(base, suffix_fmt, start_at=1)

        current = rs.ObjectName(obj_id)

        if current != new_name:
            if dry_run:
                print("[DRY] {}: '{}' -> '{}'".format(obj_id, current, new_name))
            else:
                rs.ObjectName(obj_id, new_name)
                print("Renamed: '{}' -> '{}'".format(current, new_name))
                renamed += 1

    print("")
    print("Done. Renamed {} object(s).".format(renamed))

    return renamed, name_counts


# Allow running directly inside Rhino
if __name__ == "__main__":
    rename_objects_unique(include_hidden=True, dry_run=False)