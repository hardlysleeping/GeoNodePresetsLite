# SPDX-License-Identifier: GPL-3.0-or-later
"""GN Presets Lite preferences: display only. Nothing here can edit presets."""
import bpy
from bpy.props import BoolProperty

# Headless/script use: the package is not always a registered add-on, so there
# is no preferences datablock to read. This fallback keeps one source of truth.
_fallback = {'animation_presets': False}


def prefs(context=None):
    ctx = context or bpy.context
    package = __name__.rsplit('.', 1)[0]
    addon = ctx.preferences.addons.get(package)
    return getattr(addon, 'preferences', None) if addon else None


def animation_presets(context=None):
    """True when per-preset animation snapshots are recalled."""
    settings = prefs(context)
    if settings is not None:
        return bool(getattr(settings, 'animation_presets', False))
    return bool(_fallback['animation_presets'])


def set_animation_presets(value, context=None):
    """Set the switch; used by tests and headless runs that have no add-on prefs."""
    value = bool(value)
    settings = prefs(context)
    if settings is not None:
        settings.animation_presets = value
    else:
        _fallback['animation_presets'] = value
    return value


def expanded_selector(context=None):
    settings = prefs(context)
    return bool(getattr(settings, 'expanded_selector', False)) if settings else False


class GNPL_AT_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    expanded_selector: BoolProperty(
        name='Expanded preset selector',
        description='Show presets as side-by-side buttons instead of a dropdown',
        default=False,
    )

    animation_presets: BoolProperty(
        name='Animation Presets',
        description=("Recall each preset's keyframed Geometry Nodes input values "
                     'instead of leaving animated inputs alone'),
        default=False,
    )

    def draw(self, context):
        draw_panel(self.layout, self)


def draw_panel(layout, settings):
    """Shared body so the panel can be rendered outside the preferences editor too."""
    layout.prop(settings, 'expanded_selector')
    box = layout.box()
    box.label(text='Animation Presets',
              icon='ANIM' if settings.animation_presets else 'UNLOCKED')
    box.prop(settings, 'animation_presets')
    info = box.column(align=True)
    if settings.animation_presets:
        for line in (
            'On: presets also recall keyframed',
            'float/int input values.',
            'Only the curves stored in the preset',
            'are swapped, for this modifier.',
        ):
            info.label(text=line)
        warn = box.column(align=True)
        warn.label(text='Driven inputs are never recalled:', icon='ERROR')
        warn.label(text='the driver stays, so that value is')
        warn.label(text='the same in every preset.')
    else:
        for line in (
            'Off: presets recall input values only.',
            'Animated inputs keep one animation in every preset.',
        ):
            info.label(text=line)
        keep = box.column(align=True)
        keep.label(text='Animation stored in a preset', icon='CHECKMARK')
        keep.label(text='is kept either way; turning this on')
        keep.label(text='recalls it again.')
    note = layout.box()
    note.label(text='Presets are read-only here', icon='LOCKED')
    note.label(text='Lite recalls presets shared with you.')
    note.label(text='Editing them needs the full GN Presets.')


CLASSES = (GNPL_AT_preferences,)