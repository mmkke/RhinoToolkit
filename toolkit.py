"""
Interactive command-line toolbox for inspecting and managing Rhino object names.

This module provides a persistent in-Rhino menu interface that allows users to:
    - View name statistics for model objects
    - List object names (and descriptions)
    - Rename objects to enforce unique naming
    - Toggle between operating on all model-space objects or only selected objects
    - Perform renaming in dry-run mode or apply changes permanently

The toolbox is designed as a lightweight UI wrapper around the functions in
`rename_objects` and `view_object_names`. It is intended to be run inside Rhino
via RunPythonScript or assigned to a toolbar button.

Menu Structure
--------------
The menu runs inside a loop and exposes the following options:

    SelectedObjects  : Toggle "selected-only" mode ON/OFF
    NameStats        : Print naming statistics for the working set
    ListNames        : List object names and descriptions
    RenameDry        : Show how duplicates would be renamed (no changes made)
    RenameApply      : Apply renaming operations to ensure unique names
    Exit             : Leave the toolbox loop

Selected-Only Mode
------------------
When selected-only mode is ON, the toolbox operates exclusively on the objects
currently selected in the Rhino viewport. If no objects are selected, the user
is warned and the requested operation is skipped.

Module Reloading
----------------
During each loop iteration the modules `rename_objects` and `view_object_names`
are reloaded. This is useful during development, allowing changes to those
modules to be picked up immediately without restarting Rhino.

Typical Usage
-------------
Run inside Rhino:

    _-RunPythonScript "path/to/toolbox.py"

Or assign to a toolbar button:

    ! _-RunPythonScript "path/to/toolbox.py"

"""

import rhinoscriptsyntax as rs
import rename_objects
import view_object_names

# Optional: reload modules each time (useful during development)
try:
    reload
except NameError:
    from imp import reload


def main():
    """
    Launch the interactive toolbox menu.

    The function loops indefinitely until the user selects "Exit". Each loop:
        - Reloads dependent modules (for development convenience)
        - Displays the current selected-only status
        - Prompts the user for an action
        - Validates conditions (e.g., selected-only mode must have a selection)
        - Executes the requested action
    """
    # Toggle state: False = all model objects, True = selected objects only
    selected_only = False

    while True:
        # Make sure we see latest versions of the modules
        reload(rename_objects)
        reload(view_object_names)

        mode_label = "ON" if selected_only else "OFF"
        prompt = "Choose action (Selected only: {0})".format(mode_label)

        mode = rs.GetString(
            prompt,
            "ListNames",
            ["SelectedObjects", "NameStats", "ListNames", "RenameDry", "RenameApply", "Exit"]
        )

        if not mode:
            print("Toolbox cancelled.")
            return

        if mode == "Exit":
            print("Exiting toolbox.")
            return

        if mode == "SelectedObjects":
            selected_only = not selected_only
            print("Selected only mode is now {0}".format("ON" if selected_only else "OFF"))
            print("")
            continue

        # If we are in selected-only mode, validate there is a selection
        if selected_only:
            sel = rs.SelectedObjects()
            if not sel:
                print("Selected only mode is ON but no objects are selected.")
                print("Please select some objects and run the toolbox again.")
                print("")
                continue

        if mode == "NameStats":
            view_object_names.get_object_name_stats(
                include_hidden=True,
                selected_only=selected_only
            )
            print("Name Stats Complete.\n")

        elif mode == "ListNames":
            view_object_names.list_object_info(
                include_hidden=True,
                include_description=True,
                selected_only=selected_only
            )
            print("List Names Complete.\n")

        elif mode == "RenameDry":
            rename_objects.rename_objects_unique(
                include_hidden=True,
                dry_run=True,
                selected_only=selected_only
            )
            print("Dry run complete.\n")

        elif mode == "RenameApply":
            rename_objects.rename_objects_unique(
                include_hidden=True,
                dry_run=False,
                selected_only=selected_only
            )
            print("Rename operation complete.\n")


if __name__ == "__main__":
    main()