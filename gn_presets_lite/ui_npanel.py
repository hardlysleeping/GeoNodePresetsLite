# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from .ui_common import draw_modifier_cards, geometry_modifiers


class GNPL_PT_viewport_presets(bpy.types.Panel):
    bl_idname = 'GNPL_PT_viewport_presets'
    bl_label = 'GN Presets Lite'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GN Presets Lite'

    @classmethod
    def poll(cls, context):
        return context.object is not None and bool(geometry_modifiers(context.object))

    def draw(self, context):
        draw_modifier_cards(self.layout, context.object)


CLASSES = (GNPL_PT_viewport_presets,)
