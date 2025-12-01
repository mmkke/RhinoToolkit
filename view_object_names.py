"""
Tools for inspecting and reporting object name information in a Rhino document.

This module provides two main utilities:

    - get_object_name_stats(...)
        Computes frequency statistics for all object names in the model or a
        selected subset. Reports how many objects share each name, which names
        are duplicated, and summary statistics useful for debugging large
        models or verifying naming conventions.

    - list_object_info(...)
        Prints a detailed listing of object names (and optionally descriptions)
        in the document or the current selection. Also marks occurrences of
        duplicate names for quick visual identification.

Both functions support flexible filtering options, including:
    - Operating only on selected objects
    - Including or excluding unnamed objects
    - Including or excluding hidden or locked objects
    - Optionally printing object descriptions (user text stored in Rhino)

Model-space filtering is handled via `get_model_space_objects` in `utils.py`,
ensuring that layout/page objects, lights, grips, and other non-geometry
entities are not included unless explicitly requested.

Typical usage inside Rhino:
---------------------------
    _-RunPythonScript "path/to/view_object_names.py"

Or, more commonly, these functions are called indirectly through the toolbox:

    toolbox.py  :  calls get_object_name_stats() or list_object_info()

This module is focused purely on reporting, it does not modify object names.
For renaming operations, see `rename_objects.py`.
"""

import rhinoscriptsyntax as rs
from utils import get_model_space_objects

def get_object_name_stats(selected_only=False, include_unnamed=True, include_hidden=True):
    """
    Compute statistics for object names in the Rhino document.

    Parameters
    ----------
    selected_only : bool
        Whether to only use selected objects.
    include_unnamed : bool
        Whether to include unnamed objects objects.
    include_hidden : bool
        Whether to include hidden or locked objects.

    Returns
    -------
    name_counts : dict
        Mapping from object name to frequency.
    duplicates : dict
        Mapping of only those names that appear more than once.
    ids : list
        List of object IDs included in the analysis.
    """

    # ids = rs.AllObjects(select=False, include_lights=False, include_grips=False)
    if selected_only:
        ids = rs.SelectedObjects()
    else:
        ids = get_model_space_objects(include_hidden=True,
                                include_locked=True,
                                include_grips=False,
                                include_lights=False)
    if not ids:
        print("No objects found.")
        return {}, {}, []

    # Optionally filter out hidden or locked
    if not include_hidden:
        ids = [obj_id for obj_id in ids
               if not rs.IsHidden(obj_id) and not rs.IsObjectLocked(obj_id)]

    # Keep only named objects
    if not include_unnamed:
        ids = [obj_id for obj_id in ids if (rs.ObjectName(obj_id) or "").strip()]

    # Count frequencies
    name_counts = {}
    for obj_id in ids:
        nm = rs.ObjectName(obj_id)
        name_counts[nm] = name_counts.get(nm, 0) + 1

    # Duplicate dictionary
    duplicates = dict((n, c) for (n, c) in name_counts.items() if c > 1)

    # Print stats
    print("----- Object Name Statistics -----")
    print("Total objects:", len(ids))
    print("Distinct names:", len(name_counts))
    print("Duplicate name groups:", len(duplicates))
    print("Total duplicate instances:", sum(duplicates.values()))
    print("")

    if duplicates:
        print("Duplicate name frequencies:")
        for nm, c in sorted(duplicates.items()):
            print("  Name:", nm, " Count:", c)
        print("")
    else:
        print("No duplicate names detected.")
        print("")
    print("Done.")
    return name_counts, duplicates, ids



def list_object_info(selected_only=False, include_unnamed=True, include_hidden=True, include_description=True):
    """
    List object names and descriptions without computing global stats.

    Parameters
    ----------
    selected_only : bool
        Whether to only use selected objects.
    include_unnamed : bool
        Whether to include unnamed objects objects.
    include_hidden : bool
        Whether to include hidden or locked objects.
    include_description : bool
        Whether to print object descriptions.

    Returns
    -------
    results : list of dict
        Each dict contains:
            { "id": guid, "name": string, "description": string or None }
    """

    # Collect objects
    if selected_only:
        ids = rs.SelectedObjects()
    else:
        ids = get_model_space_objects(include_hidden=True,
                                include_locked=True,
                                include_grips=False,
                                include_lights=False)
    if not ids:
        print("No objects found.")
        return []

    # Optional hidden filter
    if not include_hidden:
        ids = [obj_id for obj_id in ids
               if not rs.IsHidden(obj_id) and not rs.IsObjectLocked(obj_id)]

    # Only named
    if not include_unnamed:
        ids = [obj_id for obj_id in ids if (rs.ObjectName(obj_id) or "").strip()]
    
    print("----- Object List -----")
    print("Listing", len(ids), "named objects")
    print("")

    results = []
    seen_names = set()

    for obj_id in ids:
        name = rs.ObjectName(obj_id)

        if name in seen_names:
            print("** DUPLICATE **")
        seen_names.add(name)

        print("Object Name:", name)

        if include_description:
            desc = rs.ObjectDescription(obj_id)
            print("Object Description:", desc)
        else:
            desc = None

        print("")

        results.append({
            "id": obj_id,
            "name": name,
            "description": desc
        })

    print("Done.")
    return results


# Optional direct run
if __name__ == "__main__":
    # Compute stats
    get_object_name_stats(include_hidden=True)

    # Then list objects
    list_object_info(include_hidden=True, include_description=True)