from collections import Sequence
from dataclasses import dataclass, field

from game_data.categories import *
from game_data.effects import *


@dataclass
class Action:
    name: str
    type: type
    kind: Kind
    description: str = ""
    effects: Sequence[Effect] = field(default_factory=list)
    hit_rate: float = 1
    crit_rate: float = .05


ACTIONS = {
    1: Action("Sword Slash", FIRE, PHYSICAL, effects=[Damage(7)],
              description="Ancient warriors in an eastern land invented this method of striking down your foes efficiently and succinctly."),
    2: Action("Ambush", DARK, PHYSICAL, effects=[AmbushDamage(5)],
              description=""),
    3: Action("Explosion", FIRE, PHYSICAL, effects=[Damage(20)],
              description=""),
    4: Action("OwO", DARK, VERBAL,
              description=""),
}
