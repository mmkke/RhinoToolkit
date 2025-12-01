"""
Utility functions for retrieving Rhino model-space objects.

This module provides filtering helpers for identifying geometry objects that
exist specifically in model space (ActiveSpace.ModelSpace), excluding objects
that belong to layouts/page space. It is intended to be used by higher-level
tools-such as object name analysis, renaming utilities, or interactive
toolboxes-where predictable and consistent object sets are required.

Objects can be filtered based on:
    - Visibility (hidden or shown)
    - Lock status
    - Whether grips or lights should be included
    - RhinoCommon ActiveSpace (model vs. page/layout)

By default, this module excludes lights, grips, and other non-geometry object
types unless explicitly enabled. It returns full RhinoCommon object references
(`RhinoObject`), not GUIDs, allowing callers to access attributes, names,
geometry, and metadata directly.

Typical usage:
--------------
    from utils import get_model_space_objects
    objs = get_model_space_objects(include_hidden=False)

Used throughout:
----------------
    - rename_objects.py    (collecting objects before renaming)
    - view_object_names.py (listing names or computing statistics)
    - toolbox.py           (interactive workflow)
"""

import Rhino
from Rhino.DocObjects import ActiveSpace, ObjectType
import scriptcontext as sc


def get_model_space_objects(include_hidden=True,
                            include_locked=True,
                            include_grips=False,
                            include_lights=False):
    """
    Return a filtered list of Rhino model-space objects.

    This function iterates over all objects in the active Rhino document and
    selects only those whose Attributes.Space is ActiveSpace.ModelSpace.
    Additional optional filters allow the caller to include or exclude hidden
    objects, locked objects, display grips, and lights.

    Parameters
    ----------
    include_hidden : bool, optional
        If True (default), include hidden objects. If False, hidden objects
        are excluded.
    include_locked : bool, optional
        If True (default), include locked objects. If False, locked objects
        are excluded.
    include_grips : bool, optional
        If True, include grip objects. Default is False.
    include_lights : bool, optional
        If True, include light objects. Default is False.
    """

    result = []

    for obj in sc.doc.Objects:
        attr = obj.Attributes

        # Only model space objects
        if attr.Space != ActiveSpace.ModelSpace:
            continue

        # Skip hidden if requested
        if not include_hidden and obj.IsHidden:
            continue

        # Skip locked if requested
        if not include_locked and obj.IsLocked:
            continue

        # Skip grips, lights, and phantoms
        if not include_grips and obj.ObjectType == ObjectType.Grip:
            continue
        if not include_lights and obj.ObjectType == ObjectType.Light:
            continue

        result.append(obj)

    return result