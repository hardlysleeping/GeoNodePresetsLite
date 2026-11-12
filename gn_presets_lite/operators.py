# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-and-recall only: selecting a preset and applying its saved values."""
import bpy
from bpy.props import StringProperty
from . import presets, storage


def resolve_target(context, object_name='', modifier_name=''):
    obj = bpy.data.objects.get(object_name) if object_name else context.object
    if obj is None:
        raise ValueError('Target object not found')
    if modifier_name:
        modifier = obj.modifiers.get(modifier_name)
    else:
        modifier = getattr(context, 'modifier', None)
        if modifier is not None and modifier.id_data != obj:
            modifier = None
        if modifier is None:
            modifier = obj.modifiers.active
    if modifier is None or modifier.type != 'NODES' or modifier.node_group is None:
        raise ValueError('Target Geometry Nodes modifier not found or has no node group')
    return obj, modifier


class _Target:
    object_name: StringProperty(options={'HIDDEN'})
    modifier_name: StringProperty(options={'HIDDEN'})
    # Hidden: dialogs draw every visible operator property, and this one is the
    # *selected* preset, not something the user picks here.
    slot_id: StringProperty(default='A', options={'HIDDEN'})

    def target(self, context):
        return resolve_target(context, self.object_name, self.modifier_name)[1]

    def report_result(self, result):
        self.report({'WARNING'} if result.skipped else {'INFO'}, result.summary())


class GNPL_OT_select_preset(_Target, bpy.types.Operator):
    bl_idname = 'gnpl.select_preset'
    bl_label = 'Select Preset'
    bl_description = 'Switch this modifier to the picked preset'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return (f'Select preset {properties.slot_id}: a saved preset replaces this modifier’s '
                'unsaved live settings immediately; an empty preset keeps current settings')

    def execute(self, context):
        try:
            modifier = self.target(context)
            group = modifier.node_group
            if storage.get_slot(group, self.slot_id) is None and (
                    len(storage.slots(group)) or self.slot_id not in ('A', 'B', 'C')):
                raise ValueError('Unknown preset ID: ' + self.slot_id)
            if not modifier.id_data.is_editable:
                raise PermissionError('The target object is read-only')
            self.report_result(presets.recall(modifier, self.slot_id))
            storage.select(modifier, self.slot_id)
        except (ValueError, PermissionError, RuntimeError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class GNPL_OT_recall_preset(_Target, bpy.types.Operator):
    bl_idname = 'gnpl.recall_preset'
    bl_label = 'Recall Preset'
    bl_description = 'Reapply the selected preset to this modifier'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            modifier = self.target(context)
            self.report_result(presets.recall(modifier, self.slot_id))
        except (ValueError, PermissionError, RuntimeError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}

    @classmethod
    def description(cls, context, properties):
        slot = properties.slot_id
        try:
            modifier = resolve_target(context, properties.object_name, properties.modifier_name)[1]
            state = presets.status(modifier, slot)
        except (ValueError, KeyError, AttributeError, RuntimeError):
            return f'Reapply preset {slot} to this modifier'
        if state == 'Empty':
            return f'Preset {slot} is empty — nothing saved to restore'
        if state == 'Modified':
            return (f'Reapply preset {slot}: replace this modifier\'s unsaved edits with the saved values. '
                    'Node-group defaults stay unchanged')
        return f'Preset {slot} already matches this modifier — nothing to restore'


CLASSES = (GNPL_OT_select_preset, GNPL_OT_recall_preset)