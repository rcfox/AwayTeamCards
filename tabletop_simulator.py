from __future__ import annotations
from dataclasses import dataclass, asdict, field

# NOTE: Member names are specifically set to reflect the Tabletop Simulator JSON format.
# I know they're not how they should be named for normal Python classes.


class Base:
    def to_json(self):
        return asdict(self)


@dataclass
class Transform(Base):
    posX: float = 0
    posY: float = 0
    posZ: float = 0
    rotX: float = 0
    rotY: float = 180
    rotZ: float = 180
    scaleX: float = 0
    scaleY: float = 0
    scaleZ: float = 0


@dataclass
class Collection(Base):
    ObjectStates: List[Base]


@dataclass
class Deck(Base):
    Nickname: str
    Description: str

    Name: str = 'DeckCustom'
    Hands: bool = False
    SidewaysCard: bool = False
    Transform: Transform = field(default_factory=Transform)
    ContainedObjects: List[Base] = field(default_factory=list)
    DeckIDs: List[int] = field(default_factory=list)
    CustomDeck: Dict[str, SubDeck] = field(default_factory=dict)


@dataclass
class SubDeck(Base):
    FaceURL: str
    BackURL: str
    NumWidth: int
    NumHeight: int
    BackIsHidden: bool = False
    UniqueBack: bool = False
    Type: int = 0


@dataclass
class Card(Base):
    Nickname: str
    Description: str
    CardID: int

    Name: str = 'Card'
    Hands: bool = True
    SidewaysCard: bool = False
    Transform: Transform = field(default_factory=Transform)
