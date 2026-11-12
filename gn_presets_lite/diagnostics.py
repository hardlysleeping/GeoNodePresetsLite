# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass, field

@dataclass
class Result:
    changed: int = 0
    skipped: list = field(default_factory=list)
    message: str = ''

    def summary(self):
        text = self.message or f'{self.changed} inputs processed'
        return text + (': ' + '; '.join(self.skipped) if self.skipped else '')
