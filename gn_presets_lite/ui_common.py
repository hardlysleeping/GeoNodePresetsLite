# SPDX-License-Identifier: GPL-3.0-or-later
"""Panel drawing: pick a preset from the shared library, recall it, nothing else.

Lite reads the same library the full GN Presets add-on writes, so the preset
names, order and saved values are exactly what the author published. Editing
them needs the full add-on; here the list is only a chooser.
"""
import bpy
from . import preferences, presets, storage


def target_operator(layout, identifier, obj, modifier, slot_id, **kwargs):
    op = layout.operator(identifier, **kwargs)
    op.object_name = obj.name
    op.modifier_name = modifier.name
    op.slot_id = slot_id
    return op


def slot_items(group):
    """Presets in the author's saved order."""
    existing = storage.ordered_slots(group)
    return [(x.slot_id, x.label, x.saved) for x in existing] if existing else [
        ('A', 'A', False), ('B', 'B', False), ('C', 'C', False)]


def _context(row, obj, modifier):
    row.use_property_split = False
    row.context_pointer_set('gnp_modifier', modifier)
    row.context_pointer_set('gnp_object', obj)
    return row


def recall_available(obj, modifier, slot_id, saved):
    """True only when Recall would actually change something."""
    if not (saved and obj.is_editable):
        return False
    try:
        return presets.is_modified(modifier, slot_id)
    except (ValueError, PermissionError, RuntimeError):
        return False


def draw_preset_row(layout, obj, modifier):
    group = modifier.node_group
    selected = storage.selected_id(modifier)
    items = slot_items(group)
    item = next((x for x in items if x[0] == selected), items[0])
    selected = item[0]
    row = _context(layout.row(align=True), obj, modifier)
    if preferences.expanded_selector():
        prefix = row.row(align=True)
        prefix.alignment = 'LEFT'
        prefix.label(text='Preset')
        choices = row.row(align=True)
        choices.enabled = obj.is_editable
        for slot_id, label, _saved in items:
            target_operator(choices, 'gnpl.select_preset', obj, modifier, slot_id,
                            text=label, depress=(slot_id == selected))
        # Icon row under the wide preset buttons, with Recall centred.
        row = _context(layout.row(align=True), obj, modifier)
        split = row.split(factor=0.85)
        actions = split.row(align=True)
        actions.alignment = 'CENTER'
        split.row(align=True)
    else:
        # Label at natural width, the dropdown expands, Recall sits on the right.
        prefix = row.row(align=True)
        prefix.alignment = 'LEFT'
        prefix.label(text='Preset')
        row.row(align=True)
        controls = row.row(align=True)
        controls.alignment = 'EXPAND'
        controls.menu('GNPL_MT_presets', text=item[1])
        actions = row.row(align=True)
    recall = actions.row(align=True)
    recall.enabled = recall_available(obj, modifier, selected, item[2])
    target_operator(recall, 'gnpl.recall_preset', obj, modifier, selected,
                    text='', icon='LOOP_BACK')


def geometry_modifiers(obj):
    return [m for m in obj.modifiers if m.type == 'NODES' and m.node_group is not None]


def draw_modifier_card(layout, obj, modifier):
    """Preset chooser only, above the modifier it drives."""
    card = layout.box()
    draw_preset_row(card, obj, modifier)
    heading = card.row(align=True)
    heading.label(text=f'{modifier.name} — {modifier.node_group.name}', icon='GEOMETRY_NODES')
    # Position readout only: Lite cannot reorder, but where the preset sits in
    # the author's list is still useful context.
    items = slot_items(modifier.node_group)
    selected = next((x[0] for x in items if x[0] == storage.selected_id(modifier)), items[0][0])
    index = next((i for i, item in enumerate(items) if item[0] == selected), 0)
    controls = heading.row(align=True)
    controls.alignment = 'RIGHT'
    controls.label(text=f'{index + 1}/{len(items)}')


def draw_modifier_cards(layout, obj):
    for modifier in geometry_modifiers(obj):
        draw_modifier_card(layout, obj, modifier)


class GNPL_MT_presets(bpy.types.Menu):
    bl_idname = 'GNPL_MT_presets'
    bl_label = 'Choose Geometry Nodes preset'

    def draw(self, context):
        modifier = getattr(context, 'gnp_modifier', None)
        obj = getattr(context, 'gnp_object', None)
        if modifier is None or obj is None or modifier.node_group is None:
            self.layout.label(text='No Geometry Nodes modifier selected')
            return
        self.layout.enabled = obj.is_editable
        selected = storage.selected_id(modifier)
        for slot_id, label, saved in slot_items(modifier.node_group):
            text = f'{label} — {"Saved" if saved else "Empty (keep current values)"}'
            target_operator(self.layout, 'gnpl.select_preset', obj, modifier, slot_id,
                            text=text, icon='RADIOBUT_ON' if slot_id == selected else 'RADIOBUT_OFF')


CLASSES = (GNPL_MT_presets,)