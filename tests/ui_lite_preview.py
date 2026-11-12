# SPDX-License-Identifier: GPL-3.0-or-later
"""Screenshot the Lite panel on a file whose presets were made by the full add-on."""
import sys
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[1]
config = Path(bpy.utils.user_resource('CONFIG')).resolve()
assert (root / '.local').resolve() in config.parents, f'Unsafe non-isolated config: {config}'
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.filepaths.temporary_directory = str(root / '.local' / 'tmp')
bpy.ops.wm.open_mainfile(filepath=str(root / '.local' / 'shared.blend'))

obj = bpy.data.objects['Shared']
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
obj.modifiers.active = obj.modifiers['Shared modifier']
print('GNP_LITE_PREVIEW slots=', len(bpy.data.node_groups['Shared Geometry'].gnp_presets.slots),
      flush=True)

screen = bpy.context.window_manager.windows[0].screen
area = (next(a for a in screen.areas if a.type == 'PROPERTIES')
        if '--narrow' in sys.argv else max(screen.areas, key=lambda a: a.width * a.height))
area.type = 'PROPERTIES'
area.spaces.active.context = 'MODIFIER'


def capture():
    try:
        bpy.ops.screen.screenshot(filepath=str(root / '.local' / 'GN-Presets-Lite.png'))
        print('GNP_LITE_CAPTURED', root / '.local' / 'GN-Presets-Lite.png', flush=True)
    finally:
        bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(capture, first_interval=5)