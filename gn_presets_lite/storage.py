# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only access to the preset library stored on a node group.

Lite never creates, edits or removes preset definitions: it reads what the
data already holds, in the same RNA layout the full GN Presets add-on writes,
so a shared .blend or appended node group opens with its real presets intact.
"""
import bpy
from bpy.props import PointerProperty
from .model import GNP_Library

SELECTION_KEY = '_gnp_selected_slot'

# The property name is deliberately identical to the full add-on's: it is what
# makes a file saved with GN Presets readable here, and vice versa.
PROPERTY = 'gnp_presets'


def register():
    # If GN Presets (or another copy of Lite) already claimed the property,
    # reuse it instead of redefining it.
    if not hasattr(bpy.types.NodeTree, PROPERTY):
        setattr(bpy.types.NodeTree, PROPERTY, PointerProperty(type=GNP_Library))


def unregister():
    # Only remove the property this copy owns. Removing an RNA descriptor does
    # not delete serialized ID properties either way.
    if hasattr(bpy.types.NodeTree, PROPERTY):
        delattr(bpy.types.NodeTree, PROPERTY)


def library_available():
    return hasattr(bpy.types.NodeTree, PROPERTY)


def slots(group):
    if not group or group.bl_idname != 'GeometryNodeTree' or not library_available():
        return ()
    return group.gnp_presets.slots


def get_slot(group, slot_id):
    return next((slot for slot in slots(group) if slot.slot_id == slot_id), None)


def ordered_slots(group):
    """Presets in the order the author arranged them."""
    library = list(slots(group))
    return sorted(library, key=lambda slot: slot.order)


def selected_id(modifier):
    return str(modifier.id_data.get(SELECTION_KEY + '_' + str(modifier.persistent_uid), 'A'))


def select(modifier, slot_id):
    """Remember which preset this modifier is showing.

    This is per-modifier view state, not part of the preset definition, so it
    stays writable even when the library itself is read-only.
    """
    if not slot_id:
        raise ValueError('Preset ID must not be empty')
    modifier.id_data[SELECTION_KEY + '_' + str(modifier.persistent_uid)] = slot_id