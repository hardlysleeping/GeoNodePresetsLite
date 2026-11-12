# SPDX-License-Identifier: GPL-3.0-or-later
"""Conservative direct scalar keyframes, scoped to the owner's active slot."""
import json


def bags(action):
    for layer in getattr(action, 'layers', ()):
        for strip in layer.strips:
            for bag in getattr(strip, 'channelbags', ()):
                yield bag


def curves(action):
    if not action:
        return []
    return list(getattr(action, 'fcurves', ())) + [f for b in bags(action) for f in b.fcurves]


def target(modifier, identifier):
    pointer = getattr(modifier.properties.inputs, identifier)
    path = pointer.path_from_id('value')
    paths = {pointer.path_from_id(p) for p in ('value', 'type', 'attribute_name') if hasattr(pointer, p)}
    owner = modifier.id_data
    ad = owner.animation_data
    if not ad:
        return path, None, None
    if any(f.data_path in paths for f in ad.drivers):
        raise ValueError('drivers are protected')
    for track in ad.nla_tracks:
        for strip in track.strips:
            if any(f.data_path in paths for f in curves(strip.action)):
                raise ValueError('NLA animation is protected (including muted tracks)')
    action = ad.action
    if not action:
        return path, None, None
    if action.users > 1 or not action.is_editable or action.library:
        raise ValueError('shared/read-only Action is protected')
    if ad.use_tweak_mode or ad.action_blend_type != 'REPLACE' or ad.action_influence != 1.0:
        raise ValueError('non-direct Action evaluation is protected')
    active = [b for b in bags(action) if ad.action_slot and b.slot_handle == ad.action_slot.handle]
    matching = [(b, f) for b in active for f in b.fcurves if f.data_path in paths]
    if any(f.data_path != path for _, f in matching):
        raise ValueError('animated input mode/name is protected')
    if len(matching) > 1:
        raise ValueError('multiple layered curves are protected')
    if not matching:
        return path, None, None
    bag, fc = matching[0]
    if len(action.layers) != 1 or len(action.layers[0].strips) != 1:
        raise ValueError('multiple Action layers/strips are protected')
    if fc.modifiers or fc.sampled_points or fc.mute or fc.array_index != 0 or not fc.keyframe_points:
        raise ValueError('unsupported curve form is protected')
    return path, bag, fc


def snapshot(fc):
    if fc is None:
        return ''
    return json.dumps(dict(extrapolation=fc.extrapolation, keys=[dict(
        co=list(k.co), handle_left=list(k.handle_left), handle_right=list(k.handle_right),
        handle_left_type=k.handle_left_type, handle_right_type=k.handle_right_type,
        interpolation=k.interpolation, easing=k.easing, amplitude=k.amplitude,
        back=k.back, period=k.period, type=k.type) for k in fc.keyframe_points]), sort_keys=True)


def driven(modifier, socket):
    """True when a driver owns this input.

    Drivers are relationships, not keyframes: a preset cannot hold one, so the
    input is skipped everywhere (capture, Modified, recall) and keeps whatever
    the driver produces in every preset.
    """
    pointer = getattr(modifier.properties.inputs, socket.identifier, None)
    if pointer is None:
        return False
    data = modifier.id_data.animation_data
    if not data:
        return False
    paths = {pointer.path_from_id(p) for p in ('value', 'type', 'attribute_name') if hasattr(pointer, p)}
    return any(f.data_path in paths for f in data.drivers)


def capture(modifier, socket):
    path, bag, fc = target(modifier, socket.identifier)
    if fc and not (socket.socket_type.startswith('NodeSocketFloat') or socket.socket_type == 'NodeSocketInt'):
        raise ValueError('only scalar float/int curves are supported')
    return snapshot(fc)


def restore(modifier, record):
    path, bag, fc = target(modifier, record.identifier)
    payload = json.loads(record.curve_json) if record.curve_json else None
    if fc:
        bag.fcurves.remove(fc)
    if payload is None:
        return
    owner = modifier.id_data
    # Blender creates the correct active-slot channelbag, including for new Actions.
    owner.keyframe_insert(data_path=path, frame=payload['keys'][0]['co'][0])
    _, bag, fc = target(modifier, record.identifier)
    fc.keyframe_points.clear()
    fc.keyframe_points.add(len(payload['keys']))
    for k, data in zip(fc.keyframe_points, payload['keys']):
        k.co = data['co']
        for name in ('interpolation', 'easing', 'amplitude', 'back', 'period', 'type', 'handle_left_type', 'handle_right_type'):
            setattr(k, name, data[name])
        k.handle_left = data['handle_left']
        k.handle_right = data['handle_right']
    fc.extrapolation = payload['extrapolation']
    fc.update()
    fc.update_autoflags(owner)
