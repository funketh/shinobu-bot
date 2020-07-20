from dataclasses import dataclass

from game_data.targets import *


@dataclass
class Effect:
    pass


@dataclass
class Damage(Effect):
    amount: int
    target: Target = Targeted


@dataclass
class AmbushDamage(Damage):
    def execute(self):
        ...  # TODO
        # if (target.exhausted): crit=True
