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
objects are sorted by (name, GUID) so repeated runs yield consistent results.

This module is intended to be called from interactive tooling such as
`toolbox.py`, but each function can also be used independently.
"""

import rhinoscriptsyntax as rs
from utils import get_model_space_objects


def name_in_use(name):
    """
    Return True if any object in the document already uses 'name'.

    Note
    ----
    This helper uses rs.ObjectsByName and is kept for compatibility and
    external callers. The main renaming function uses a cached name set
    for performance and does not call this in its inner loop.
    """
    objs = rs.ObjectsByName(name)
    return bool(objs)


def next_unique_name(base, suffix_fmt, start_at=2):
    """
    Return a unique object name by appending an incrementing numeric suffix.

    This version uses the live document via name_in_use and is kept for
    compatibility. The optimized renaming routine uses an internal cached
    name set instead.

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


def _build_used_name_set():
    """
    Build a set of all currently used object names in the document.

    Returns
    -------
    used_names : set of str
        All non-empty names in the document.
    """
    used = set()
    all_ids = rs.AllObjects(select=False, include_lights=False, include_grips=False)
    if not all_ids:
        return used

    for oid in all_ids:
        nm = rs.ObjectName(oid)
        if nm:
            used.add(nm)
    return used


def _next_unique_with_cache(base, suffix_fmt, used_names, next_suffix_dict):
    """
    Fast helper: find the next available name for 'base' using only
    Python data structures (no Rhino queries).

    Parameters
    ----------
    base : str
        Base name to modify.
    suffix_fmt : str
        Format string like " {num:03d}".
    used_names : set
        Set of all names already known to be in use.
    next_suffix_dict : dict
        Mapping base -> next suffix number to try.

    Returns
    -------
    new_name : str
        A name that is not in used_names (and is reserved in used_names).
    """
    base = base or "Object"
    # Start from recorded suffix, or 1 if not present
    n = next_suffix_dict.get(base, 1)

    while True:
        candidate = "{}{}".format(base, suffix_fmt.format(num=n))
        if candidate not in used_names:
            next_suffix_dict[base] = n + 1
            used_names.add(candidate)
            return candidate
        n += 1


def rename_objects_unique(selected_only=False,
                          include_unnamed=True,
                          include_hidden=True,
                          dry_run=False,
                          suffix_fmt=" {num:03d}",
                          verbose=True):
    """
    Rename all Rhino objects so that each named object has a unique name.
    Reports statistics before renaming.

    This optimized implementation avoids repeated document lookups inside the
    renaming loop by:
        - Caching the current names for all working objects
        - Building a document-wide set of used names once
        - Using purely Python set membership for name availability checks

    Parameters
    ----------
    selected_only : bool, optional
        Whether to only use selected objects.
    include_unnamed : bool, optional
        Whether to include unnamed objects.
    include_hidden : bool, optional
        Whether to include hidden or locked objects.
    dry_run : bool, optional
        If True, only report renaming actions (no changes applied).
    suffix_fmt : str, optional
        Formatting for numeric suffix, e.g. " {num:03d}" or "-{num:03d}".

    Returns
    -------
    renamed_count : int
        Number of renamed objects (0 in dry_run mode).
    stats : dict
        Statistics about names and duplicates (name -> count).
    """

    # ------------------------------------------------------------
    # Collect object IDs (always work with GUIDs)
    # ------------------------------------------------------------
    if selected_only:
        ids = rs.SelectedObjects()
    else:
        # get_model_space_objects returns Rhino objects; convert to GUIDs
        objs = get_model_space_objects(include_hidden=True,
                                       include_locked=True,
                                       include_grips=False,
                                       include_lights=False)
        ids = [obj.Id for obj in objs]

    if not ids:
        print("No objects found.")
        return 0, {}

    # Optional filtering: unnamed
    if not include_unnamed:
        ids = [obj_id for obj_id in ids
               if (rs.ObjectName(obj_id) or "").strip()]

    # Optional filtering: hidden / locked
    if not include_hidden:
        ids = [obj_id for obj_id in ids
               if not rs.IsHidden(obj_id) and not rs.IsObjectLocked(obj_id)]

    if not ids:
        print("No named objects found.")
        return 0, {}

    # ------------------------------------------------------------
    # Cache names for working set and count frequencies
    # ------------------------------------------------------------
    name_counts = {}
    name_by_id = {}

    for obj_id in ids:
        nm = rs.ObjectName(obj_id) or "Object"
        name_by_id[obj_id] = nm
        name_counts[nm] = name_counts.get(nm, 0) + 1

    # Detect duplicates (base names with count > 1)
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

    if dup_names:
        print("Duplicate name frequencies:")
        for nm, c in sorted(dup_names.items()):
            print("  Name:", nm, " Count:", c)
        print("")
    else:
        print("No duplicates detected.")
        print("")

    # If no duplicates, nothing to rename
    if not dup_names:
        print("All object names are already unique.")
        return 0, name_counts

    # ------------------------------------------------------------
    # Prepare for renaming (optimized path)
    # ------------------------------------------------------------
    # Build a global set of all names currently in use anywhere in the doc
    used_names = _build_used_name_set()

    # Ensure working set names are in used_names
    # (in case include_unnamed filtered anything weird)
    for nm in name_counts:
        if nm:
            used_names.add(nm)

    renamed = 0
    would_rename = 0
    assigned_base_once = set()
    next_suffix = {}

    # Deterministic ordering: (current name, GUID string)
    ids_sorted = sorted(ids, key=lambda i: (name_by_id[i], str(i)))

    # Determine whether to print detailed output
    large_dataset = len(ids) > 500
    detailed = verbose and not large_dataset

    if large_dataset and verbose:
        print("Large dataset detected ({} objects). Suppressing detailed "
              "per-object printing for performance.\n".format(len(ids)))

    print("----- Renaming Duplicates -----")

    renamed = 0
    would_rename = 0
    assigned_base_once = set()
    next_suffix = {}

    rs.EnableRedraw(False)
    try:
        for obj_id in ids_sorted:
            base = name_by_id[obj_id]

            if base not in dup_names:
                continue

            # Determine new name
            if base not in assigned_base_once:
                if base not in used_names:
                    new_name = base
                    used_names.add(new_name)
                else:
                    new_name = _next_unique_with_cache(base, suffix_fmt,
                                                       used_names, next_suffix)
                assigned_base_once.add(base)
            else:
                new_name = _next_unique_with_cache(base, suffix_fmt,
                                                   used_names, next_suffix)

            current = name_by_id[obj_id]

            if current != new_name:
                if dry_run:
                    if detailed:
                        print("[DRY] {}: '{}' -> '{}'".format(obj_id, current, new_name))
                    would_rename += 1
                else:
                    rs.ObjectName(obj_id, new_name)
                    if detailed:
                        print("Renamed: '{}' -> '{}'".format(current, new_name))
                    renamed += 1
    finally:
        rs.EnableRedraw(True)

    print("")

    # Summary only
    if dry_run:
        print("Dry run complete. {} object(s) would have been renamed.".format(would_rename))
        if not detailed:
            print("(Use verbose=True for detailed printing on small datasets.)")
        return 0, name_counts
    else:
        print("Done. Renamed {} object(s).".format(renamed))
        if not detailed:
            print("(Use verbose=True for detailed printing on small datasets.)")
        return renamed, name_counts


# Allow running directly inside Rhino
if __name__ == "__main__":
    rename_objects_unique(include_hidden=True, dry_run=False)