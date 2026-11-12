# SPDX-License-Identifier: GPL-3.0-or-later
"""Host runner: python3 tests/run_lite_tests.py

Two processes on purpose: the fixture is written by the full GN Presets add-on,
then read by Lite with nothing but Lite importable. GNP_BLENDER points the suite
at any Blender binary; GNP_FULL_PATH points at the full add-on's repo.
"""
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
logs = root / '.local' / 'lite_test_logs'
logs.mkdir(parents=True, exist_ok=True)
profile = root / '.local' / 'lite-profile'
for part in ('config', 'extensions', 'scripts'):
    (profile / part).mkdir(parents=True, exist_ok=True)

override = os.environ.get('GNP_BLENDER')
profile_env = {'BLENDER_USER_CONFIG': str(profile / 'config'),
               'BLENDER_USER_EXTENSIONS': str(profile / 'extensions'),
               'BLENDER_USER_SCRIPTS': str(profile / 'scripts')}
shared = root / '.local' / 'shared.blend'


def build_cmd(script, args):
    if override:
        return ([override, '--background', '--factory-startup', '--offline-mode',
                 '--python-exit-code', '1', '--python', str(script), *args],
                dict(os.environ, **profile_env))
    return (['flatpak', 'run'] + ['--env=' + k + '=' + v for k, v in profile_env.items()]
            + ['org.blender.Blender', '--background', '--factory-startup', '--offline-mode',
               '--python-exit-code', '1', '--python', str(script), *args],
            None)


commands = [('write_fixture', root / 'tests' / 'make_shared_fixture.py', [str(shared)]),
            ('read_with_lite', root / 'tests' / 'test_lite.py', [])]
summary = []
for name, script, args in commands:
    cmd, env = build_cmd(script, args)
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
    output = result.stdout + result.stderr
    (logs / (name + '.log')).write_text(output)
    lines = [line for line in output.splitlines() if line.startswith('GNP_')]
    print('\n'.join(lines) if lines else output, flush=True)
    summary.append(dict(phase=name, returncode=result.returncode, results=lines))
    if result.returncode:
        print(output, flush=True)
        raise SystemExit(result.returncode)
print('GNP_ALL_LITE_PROCESSES_PASSED', len(summary), flush=True)