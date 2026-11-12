# SPDX-License-Identifier: GPL-3.0-or-later
"""Fixture writer: save presets with the full GN Presets, then hand the file over.

Run with the full add-on on sys.path (GNP_FULL_PATH or ../../GeoNodePresets).
"""
import os
import sys
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[1]
full = Path(os.environ.get('GNP_FULL_PATH', root.parent / 'GeoNodePresets'))
sys.path.insert(0, str(full))
import gn_presets
from gn_presets import presets as full_presets, storage as full_storage

gn_presets.register()

mesh = bpy.data.meshes.new('SharedMesh')
obj = bpy.data.objects.new('Shared', mesh)
bpy.context.collection.objects.link(obj)

group = bpy.data.node_groups.new('Shared Geometry', 'GeometryNodeTree')
group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
radius = group.interface.new_socket(name='Radius', in_out='INPUT', socket_type='NodeSocketFloat')
radius.default_value = 1.0
radius.min_value = 0.0
radius.max_value = 100.0
radius.force_non_field = True
count = group.interface.new_socket(name='Count', in_out='INPUT', socket_type='NodeSocketInt')
count.default_value = 4
count.force_non_field = True
nodes_in = group.nodes.new('NodeGroupInput')
nodes_out = group.nodes.new('NodeGroupOutput')
group.links.new(nodes_in.outputs['Geometry'], nodes_out.inputs['Geometry'])

mod = obj.modifiers.new('Shared modifier', 'NODES')
mod.node_group = group


def set_inputs(radius_value, count_value):
    getattr(mod.properties.inputs, radius.identifier).value = radius_value
    getattr(mod.properties.inputs, count.identifier).value = count_value


# A: 3.5 / 12, B: 0.5 / 40, then a fourth preset added and renamed out of order.
set_inputs(3.5, 12)
full_presets.save(mod, 'A')
set_inputs(0.5, 40)
full_presets.save(mod, 'B')
slot = full_storage.add_slot(group, 'Wide')
set_inputs(9.0, 7)
full_presets.save(mod, slot.slot_id)

# Leave the file selected on B so the fixture also carries per-modifier state.
full_storage.select(mod, 'B')
set_inputs(2.0, 20)

out = Path(sys.argv[-1]) if sys.argv[-1].endswith('.blend') else root / '.local' / 'shared.blend'
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out), check_existing=False)

print('GNP_FIXTURE_SAVED', out, flush=True)
print('GNP_FIXTURE_SLOTS', [(s.slot_id, s.label, s.saved) for s in full_storage.ordered_slots(group)],
      flush=True)
print('GNP_FIXTURE_SELECTED', full_storage.selected_id(mod), flush=True)
gn_presets.unregister()