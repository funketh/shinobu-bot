from dataclasses import dataclass


@dataclass
class Type:
    name: str


FIRE = Type("Fire")
STORM = Type("Storm")
WATER = Type("Water")
LEAF = Type("Leaf")
DARK = Type("Dark")
LIGHT = Type("Light")
DRAGON = Type("Dragon")


@dataclass
class Kind:
    name: str


PHYSICAL = Kind("physical")
VERBAL = Kind("verbal")
