# SPDX-License-Identifier: GPL-3.0-or-later
"""GN Presets Lite: recall presets someone shared with you, without editing them."""


def register():
    import bpy
    from . import model, storage, operators, ui_common, ui_modifier, ui_npanel, preferences
    # If the full add-on is installed, its model classes already exist: reuse
    # them instead of registering a second copy of the same RNA types.
    own_model = not hasattr(bpy.types, 'GNP_Library')
    registered = []
    try:
        if own_model:
            for cls in model.CLASSES:
                bpy.utils.register_class(cls)
                registered.append(cls)
        storage.register()
        for cls in (operators.CLASSES + ui_common.CLASSES + ui_modifier.CLASSES
                    + ui_npanel.CLASSES + preferences.CLASSES):
            bpy.utils.register_class(cls)
            registered.append(cls)
    except Exception:
        storage.unregister()
        for cls in reversed(registered):
            bpy.utils.unregister_class(cls)
        raise


def unregister():
    import bpy
    from . import model, storage, operators, ui_common, ui_modifier, ui_npanel, preferences
    for cls in reversed(operators.CLASSES + ui_common.CLASSES + ui_modifier.CLASSES
                        + ui_npanel.CLASSES + preferences.CLASSES):
        bpy.utils.unregister_class(cls)
    storage.unregister()
    # Only remove the model types this copy registered itself.
    for cls in reversed(model.CLASSES):
        if getattr(cls, 'is_registered', False):
            bpy.utils.unregister_class(cls)