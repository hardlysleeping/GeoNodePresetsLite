# SPDX-License-Identifier: GPL-3.0-or-later
"""Read exposed interface sockets; never write interface defaults."""
def inputs(group):
    if group is None:
        return ()
    return tuple(item for item in group.interface.items_tree
                 if item.item_type == 'SOCKET' and item.in_out == 'INPUT'
                 and item.socket_type not in {'NodeSocketGeometry', 'NodeSocketVirtual'}
                 and not getattr(item, 'hide_in_modifier', False))

def animated(modifier, identifier):
    owner = modifier.id_data
    data = owner.animation_data
    if not data:
        return False
    pointer = getattr(modifier.properties.inputs, identifier, None)
    if pointer is None:
        return False
    paths = {pointer.path_from_id(prop) for prop in ('value', 'type', 'attribute_name')
             if hasattr(pointer, prop)}
    curves = list(data.drivers)
    action = data.action
    if action:
        # Blender 4.4+ layered/slotted actions, plus legacy compatibility.
        if hasattr(action, 'fcurves'):
            curves.extend(action.fcurves)
        for layer in getattr(action, 'layers', ()):
            for strip in layer.strips:
                for bag in getattr(strip, 'channelbags', ()):
                    curves.extend(bag.fcurves)
    # Include NLA actions, even muted tracks: do not destroy authored control.
    for track in data.nla_tracks:
        for strip in track.strips:
            action = strip.action
            if action:
                for layer in getattr(action, 'layers', ()):
                    for action_strip in layer.strips:
                        for bag in getattr(action_strip, 'channelbags', ()):
                            curves.extend(bag.fcurves)
    return any(curve.data_path in paths for curve in curves)
