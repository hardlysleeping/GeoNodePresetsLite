# SPDX-License-Identifier: GPL-3.0-or-later
"""Serialized RNA model; definitions belong to the real NodeTree ID."""
import bpy
from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty,
                       FloatVectorProperty, PointerProperty, CollectionProperty)

class GNP_Value(bpy.types.PropertyGroup):
    curve_json: StringProperty()
    identifier: StringProperty()
    socket_type: StringProperty()
    kind: StringProperty()
    float_value: FloatProperty()
    int_value: IntProperty()
    bool_value: BoolProperty()
    string_value: StringProperty()
    vector_value: FloatVectorProperty(size=4)
    vector_size: IntProperty(default=3)
    ref_was_set: BoolProperty()
    object_ref: PointerProperty(type=bpy.types.Object)
    collection_ref: PointerProperty(type=bpy.types.Collection)
    material_ref: PointerProperty(type=bpy.types.Material)
    image_ref: PointerProperty(type=bpy.types.Image)
    font_ref: PointerProperty(type=bpy.types.VectorFont)
    sound_ref: PointerProperty(type=bpy.types.Sound)
    has_attribute_mode: BoolProperty()
    attribute_mode: StringProperty()
    has_attribute_name: BoolProperty()
    attribute_name: StringProperty()

class GNP_Slot(bpy.types.PropertyGroup):
    slot_id: StringProperty()
    label: StringProperty()
    order: IntProperty()
    saved: BoolProperty()
    values: CollectionProperty(type=GNP_Value)

class GNP_Library(bpy.types.PropertyGroup):
    schema_version: IntProperty(default=1)
    slots: CollectionProperty(type=GNP_Slot)

CLASSES = (GNP_Value, GNP_Slot, GNP_Library)
