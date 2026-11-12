# SPDX-License-Identifier: GPL-3.0-or-later
"""Recall tuned preset values onto a modifier. Definitions are never written."""
import bpy
from . import storage, sockets, codecs, animation, preferences
from .diagnostics import Result

def refresh(modifier):
    """Re-evaluate the modifier so recalled values reach the viewport immediately."""
    obj = modifier.id_data
    # Bare update_tag also tags geometry; refresh={'OBJECT'} does NOT invalidate
    # the Geometry Nodes modifier, which is why the viewport used to stay stale.
    obj.update_tag()
    try:
        bpy.context.view_layer.update()
        bpy.context.evaluated_depsgraph_get().update()
    except (AttributeError, RuntimeError):
        pass
    for window in getattr(bpy.context.window_manager, 'windows', ()):
        for area in window.screen.areas:
            if area.type in {'VIEW_3D', 'PROPERTIES', 'NODE_EDITOR'}:
                area.tag_redraw()


def group_for(modifier):
    if modifier is None or modifier.type != 'NODES' or modifier.node_group is None:
        raise ValueError('Choose a Geometry Nodes modifier with an assigned node group')
    return modifier.node_group


def recall(modifier, slot_id):
    group = group_for(modifier)
    slot = storage.get_slot(group, slot_id)
    result = Result(message='Empty preset: current inputs unchanged')
    if slot is None or not slot.saved:
        return result
    if not modifier.id_data.is_editable:
        raise PermissionError('The target object is read-only')
    animated = preferences.animation_presets()
    exposed = {s.identifier: s for s in sockets.inputs(group)}

    def controlled(identifier):
        return not animated and sockets.animated(modifier, identifier)

    for record in slot.values:
        # Preflight stays tolerant on purpose: the apply phase below is what
        # reports each skip, so a preset saved against an older interface still
        # restores every input it can instead of aborting the whole recall.
        socket = exposed.get(record.identifier)
        if socket is None or socket.socket_type != record.socket_type:
            continue
        if controlled(record.identifier):
            continue
        try:
            codecs.value(record)
            animation.target(modifier, record.identifier)
        except (ValueError, TypeError, AttributeError, RuntimeError):
            continue
    for record in slot.values:
        socket = exposed.get(record.identifier)
        try:
            if socket is None: raise ValueError('input removed or hidden')
            if socket.socket_type != record.socket_type: raise ValueError('socket type changed')
            if controlled(record.identifier):
                # Leave the live animation exactly as it is; the preset keeps its
                # stored curve for when Animation Presets is turned back on.
                reason = ('driver keeps this input the same in every preset'
                          if animation.driven(modifier, socket) else
                          'animation stays the same in every preset (Animation Presets off)')
                result.skipped.append(f'{socket.name}: {reason}')
                continue
            animation.target(modifier, record.identifier)
            value = codecs.value(record)
            pointer = getattr(modifier.properties.inputs, record.identifier)
            if pointer.bl_rna.properties['value'].is_readonly: raise ValueError('input is read-only')
            if animated:
                animation.restore(modifier, record)
            pointer.value = value
            if record.has_attribute_mode and hasattr(pointer, 'type'):
                pointer.type = record.attribute_mode
            if record.has_attribute_name and hasattr(pointer, 'attribute_name'):
                pointer.attribute_name = record.attribute_name
            result.changed += 1
        except (ValueError, TypeError, AttributeError, RuntimeError) as exc:
            result.skipped.append(f'{getattr(socket, "name", record.identifier)}: {exc}')
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    refresh(modifier)
    result.message = f'Recalled preset {slot.label}'
    return result

def compare(modifier, slot_id=None):
    """Compare the live inputs with a saved snapshot.

    Returns 'same', 'differ', or 'unknown'. 'unknown' means some stored input
    can no longer be compared because its animation moved into a form this
    add-on refuses to read (shared Action, NLA track, muted curve, curve
    modifier, ...). That is not an unsaved edit: the add-on has nothing to
    compare, and Recall/switch will skip that socket and say so.
    """
    if modifier is None or modifier.type != 'NODES': return 'same'
    slot = storage.get_slot(modifier.node_group, slot_id or storage.selected_id(modifier))
    if slot is None or not slot.saved: return 'same'
    animated = preferences.animation_presets()
    unknown = False
    exposed = {s.identifier: s for s in sockets.inputs(modifier.node_group)}
    for record in slot.values:
        socket = exposed.get(record.identifier)
        if socket is None or socket.socket_type != record.socket_type: return 'differ'
        # A driver owns the input and a preset never writes it: it can neither
        # match nor differ, so it must not make the preset look Modified.
        if animation.driven(modifier, socket): continue
        # With Animation Presets off an animated socket has no comparable stored
        # state: reading it would change every frame and would let autosave
        # overwrite a stored curve. Never report it as modified.
        if not animated and sockets.animated(modifier, record.identifier):
            continue
        try:
            data = codecs.read(modifier, socket)
            curve = animation.capture(modifier, socket) if animated else ''
            if animated and curve != record.curve_json: return 'differ'
            if not curve and not codecs.equal(data['value'], codecs.value(record)): return 'differ'
            if record.has_attribute_mode and data['attribute_mode'] != record.attribute_mode: return 'differ'
            if record.has_attribute_name and data['attribute_name'] != record.attribute_name: return 'differ'
        except (ValueError, TypeError, AttributeError, RuntimeError):
            unknown = True
    # A newly added supported input was not part of the snapshot.
    recorded = {r.identifier for r in slot.values}
    for socket in exposed.values():
        if socket.identifier not in recorded and codecs.kind(socket) and not sockets.animated(modifier, socket.identifier):
            return 'differ'
    return 'unknown' if unknown else 'same'

def is_modified(modifier, slot_id=None):
    return compare(modifier, slot_id) == 'differ'

def status(modifier, slot_id=None):
    slot = storage.get_slot(getattr(modifier, 'node_group', None), slot_id or storage.selected_id(modifier))
    if slot is None or not slot.saved: return 'Empty'
    return 'Modified' if compare(modifier, slot_id) == 'differ' else 'Saved'
