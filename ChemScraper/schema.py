from monty.json import MSONable

from ChemScraper.settings import *


class Compound(MSONable):

    def __init__(
            self, cid: int,
            smiles: str = None,
            inchi: str = None,
            iupac: str = None,
            properties: dict = None,
    ):
        self.iupac = iupac
        self.inchi = inchi
        self.smiles = smiles
        self.cid = cid
        if properties is None:
            properties = dict()
        self.properties = properties

    @property
    def identifier(self):
        return getattr(self, MainIdentifierType)

    def __gt__(self, other):
        return self.__repr__().__gt__(other.__repr__())

    def __lt__(self, other):
        return self.__repr__().__lt__(other.__repr__())

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __repr__(self):
        return "{} - {}: {}".format(self.__class__.__name__, MainIdentifierType, self.identifier)
