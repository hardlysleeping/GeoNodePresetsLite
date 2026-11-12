# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed, blend-native value codecs. ID references are RNA pointers, never names."""
import math

REFS = {'NodeSocketObject': 'object_ref', 'NodeSocketCollection': 'collection_ref',
        'NodeSocketMaterial': 'material_ref', 'NodeSocketImage': 'image_ref',
        'NodeSocketFont': 'font_ref', 'NodeSocketSound': 'sound_ref'}

def kind(socket):
    t = socket.socket_type
    if t in REFS: return 'REF'
    if t.startswith('NodeSocketFloat'): return 'FLOAT'
    if t == 'NodeSocketInt': return 'INT'
    if t == 'NodeSocketBool': return 'BOOL'
    if t.startswith('NodeSocketVector'): return 'VECTOR'
    if t == 'NodeSocketColor': return 'COLOR'
    if t == 'NodeSocketString': return 'STRING'
    if t == 'NodeSocketMenu': return 'MENU'
    return None

def read(modifier, socket):
    key = socket.identifier
    pointer = getattr(modifier.properties.inputs, key, None)
    if pointer is None or 'value' not in pointer.bl_rna.properties:
        raise ValueError('input has no writable modifier value')
    if pointer.bl_rna.properties['value'].is_readonly:
        raise ValueError('input value is read-only')
    value = pointer.value
    k = kind(socket)
    if k is None: raise ValueError('unsupported socket type ' + socket.socket_type)
    if k in ('VECTOR', 'COLOR'): value = tuple(value)
    return dict(identifier=key, socket_type=socket.socket_type, kind=k, value=value,
                has_attribute_mode=hasattr(pointer, 'type'),
                attribute_mode=str(getattr(pointer, 'type', '')),
                has_attribute_name=hasattr(pointer, 'attribute_name'),
                attribute_name=str(getattr(pointer, 'attribute_name', '')))

def store(record, data):
    for key in ('identifier', 'socket_type', 'kind', 'has_attribute_mode', 'attribute_mode', 'has_attribute_name', 'attribute_name'):
        setattr(record, key, data[key])
    value, k = data['value'], data['kind']
    if k == 'REF':
        record.ref_was_set = value is not None
        setattr(record, REFS[record.socket_type], value)
    elif k in ('VECTOR', 'COLOR'):
        record.vector_size = len(value)
        record.vector_value = tuple(value) + (0.0,) * (4 - len(value))
    else:
        setattr(record, {'FLOAT':'float_value','INT':'int_value','MENU':'string_value','BOOL':'bool_value','STRING':'string_value'}[k], value)

def value(record):
    k = record.kind
    if k == 'REF':
        result = getattr(record, REFS[record.socket_type])
        if record.ref_was_set and result is None:
            raise ValueError('saved reference was deleted or is missing')
        return result
    if k in ('VECTOR', 'COLOR'): return tuple(record.vector_value[:record.vector_size])
    return getattr(record, {'FLOAT':'float_value','INT':'int_value','MENU':'string_value','BOOL':'bool_value','STRING':'string_value'}[k])

def equal(a, b):
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)
    return a == b
