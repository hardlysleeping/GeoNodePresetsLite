# SPDX-License-Identifier: GPL-3.0-or-later
"""Lite contract: read a shared library, recall it, and never write to it."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import bpy

root = Path(__file__).resolve().parents[1]
config = Path(bpy.utils.user_resource('CONFIG')).resolve()
assert (root / '.local').resolve() in config.parents, f'Unsafe non-isolated config: {config}'
sys.path.insert(0, str(root))
import gn_presets_lite
from gn_presets_lite import operators, presets, storage, ui_common

SHARED = root / '.local' / 'shared.blend'
WRITE_OPERATORS = ('save', 'add', 'rename', 'delete', 'move', 'clear_all', 'toggle_autosave')


class Layout:
    """Minimal UIListLayout stand-in that records what would be drawn."""

    def __init__(self, events, parent=None):
        self.events = events
        self.enabled = True
        self.alignment = None
        self.parent = parent
        self.children = []
        if parent is not None:
            parent.children.append(self)

    def _child(self):
        child = Layout(self.events, self)
        child.enabled = self.enabled
        child.alignment = self.alignment
        return child

    def row(self, **kwargs):
        return self._child()

    def split(self, **kwargs):
        return self._child()

    def column(self, **kwargs):
        return self._child()

    def box(self):
        self.events.append(('box',))
        return self._child()

    def label(self, **kwargs):
        self.events.append(('label', kwargs.get('text', '')))

    def separator(self, **kwargs):
        self.events.append(('separator', kwargs.get('factor', 1.0)))

    def menu(self, identifier, **kwargs):
        self.events.append(('menu', identifier, kwargs.get('text', ''), self))

    def operator(self, identifier, **kwargs):
        op = SimpleNamespace()
        self.events.append(('operator', identifier, op, kwargs, self.enabled, self, self.parent))
        return op

    def prop(self, pointer, property, **kwargs):
        self.events.append(('prop', pointer, property, kwargs.get('text', '')))

    def context_pointer_set(self, *args):
        pass


def value_of(modifier, socket_name):
    group = modifier.node_group
    identifier = next(s.identifier for s in group.interface.items_tree
                      if getattr(s, 'in_out', None) == 'INPUT' and s.item_type == 'SOCKET'
                      and s.name == socket_name)
    return getattr(modifier.properties.inputs, identifier).value


class LiteContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gn_presets_lite.register()

    @classmethod
    def tearDownClass(cls):
        gn_presets_lite.unregister()

    def setUp(self):
        if not SHARED.is_file():
            self.skipTest(f'fixture missing: {SHARED}')
        bpy.ops.wm.open_mainfile(filepath=str(SHARED))
        self.obj = bpy.data.objects['Shared']
        bpy.context.view_layer.objects.active = self.obj
        self.modifier = self.obj.modifiers['Shared modifier']
        self.group = self.modifier.node_group
        self.events = []

    # --- reading -------------------------------------------------------
    def test_shared_library_is_readable(self):
        slots = storage.ordered_slots(self.group)
        # A and B were saved, C is an untouched fixed slot, Wide was added last.
        self.assertEqual([slot.label for slot in slots], ['A', 'B', 'C', 'Wide'])
        self.assertEqual([slot.saved for slot in slots], [True, True, False, True])
        self.assertEqual(len(slots[3].values), 2, 'saved values must survive the hand-off')
        self.assertEqual(storage.selected_id(self.modifier), 'B')

    def test_recall_applies_saved_values(self):
        before = (value_of(self.modifier, 'Radius'), value_of(self.modifier, 'Count'))
        self.assertEqual(before, (2.0, 20), 'fixture starts on unsaved live values')
        result = presets.recall(self.modifier, 'B')
        self.assertEqual((value_of(self.modifier, 'Radius'), value_of(self.modifier, 'Count')),
                         (0.5, 40))
        self.assertEqual(result.changed, 2)
        presets.recall(self.modifier, 'A')
        self.assertEqual((value_of(self.modifier, 'Radius'), value_of(self.modifier, 'Count')),
                         (3.5, 12))

    def test_recall_never_changes_the_stored_preset(self):
        def snapshot():
            return [(slot.slot_id, slot.label, slot.order, slot.saved,
                     [(v.identifier, v.float_value, v.int_value) for v in slot.values])
                    for slot in storage.ordered_slots(self.group)]
        before = snapshot()
        presets.recall(self.modifier, 'A')
        presets.recall(self.modifier, 'B')
        self.assertEqual(snapshot(), before)

    def test_select_operator_switches_preset(self):
        with bpy.context.temp_override(object=self.obj, active_object=self.obj):
            result = bpy.ops.gnpl.select_preset(object_name=self.obj.name,
                                                modifier_name=self.modifier.name, slot_id='A')
        self.assertEqual(result, {'FINISHED'})
        self.assertEqual(storage.selected_id(self.modifier), 'A')
        self.assertEqual(value_of(self.modifier, 'Radius'), 3.5)

    def test_unknown_preset_is_refused(self):
        # A slot that does not exist is an error, not a silent no-op.
        with bpy.context.temp_override(object=self.obj, active_object=self.obj):
            with self.assertRaises(RuntimeError):
                bpy.ops.gnpl.select_preset(object_name=self.obj.name,
                                           modifier_name=self.modifier.name, slot_id='ZZ')
        before = value_of(self.modifier, 'Radius')
        result = presets.recall(self.modifier, 'C')
        self.assertEqual(result.changed, 0, 'an empty preset must not touch the modifier')
        self.assertEqual(value_of(self.modifier, 'Radius'), before)

    # --- not writing ---------------------------------------------------
    def test_no_write_operators_exist(self):
        names = set()
        for cls in operators.CLASSES:
            names.add(cls.bl_idname)
            self.assertFalse(any(word in cls.bl_idname for word in WRITE_OPERATORS),
                             f'{cls.bl_idname} would write to the library')
        self.assertEqual(names, {'gnpl.select_preset', 'gnpl.recall_preset'})
        available = dir(bpy.ops.gnpl)
        for word in WRITE_OPERATORS:
            self.assertNotIn(word, available, f'bpy.ops.gnpl.{word} must not exist in Lite')

    def test_storage_exposes_no_mutators(self):
        for name in ('ensure_slots', 'add_slot', 'rename_slot', 'delete_slot', 'move_slot',
                     'clear_library', 'set_autosave', 'repair_slots', 'free_label'):
            self.assertFalse(hasattr(storage, name), f'storage.{name} still exists in Lite')
        self.assertFalse(hasattr(presets, 'save'), 'presets.save still exists in Lite')

    def test_panel_offers_only_choose_and_recall(self):
        ui_common.draw_modifier_cards(Layout(self.events), self.obj)
        ops = [e[1] for e in self.events if e[0] == 'operator']
        self.assertTrue(ops)
        self.assertEqual(set(ops), {'gnpl.recall_preset'})
        menus = [e for e in self.events if e[0] == 'menu']
        self.assertEqual([m[1] for m in menus], ['GNPL_MT_presets'])
        # No reorder arrows, no position buttons: the readout is a plain label.
        self.assertFalse(any(e[0] == 'operator' and e[1].endswith('move_preset')
                             for e in self.events))

    def test_menu_lists_presets_without_edit_entries(self):
        events = []
        stub = SimpleNamespace(layout=Layout(events))
        context = SimpleNamespace(gnp_modifier=self.modifier, gnp_object=self.obj)
        ui_common.GNPL_MT_presets.draw(stub, context)
        ops = [e[1] for e in events if e[0] == 'operator']
        self.assertEqual(set(ops), {'gnpl.select_preset'})
        texts = [e[3].get('text', '') for e in events if e[0] == 'operator']
        self.assertEqual(len(texts), 4, texts)
        self.assertFalse(any('New Preset' in t or 'Rename' in t for t in texts))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LiteContract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print('GNP_LITE_RESULT tests=%d failures=%d errors=%d skipped=%d'
          % (result.testsRun, len(result.failures), len(result.errors), len(result.skipped)),
          flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)