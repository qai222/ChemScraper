import base64
import collections
import re
from io import BytesIO

import rdkit.Chem
from rdkit.Chem import MolToSmiles, MolToInchi, MolFromSmiles, MolFromSmarts
from rdkit.Chem.Draw import MolToImage
from rdkit.Chem.inchi import MolFromInchi


def inchi2smiles(inchi: str) -> str:
    return MolToSmiles(MolFromInchi(inchi))


def smiles2inchi(smi: str) -> str:
    return MolToInchi(MolFromSmiles(smi))


def neutralize_atoms(mol):
    pattern = MolFromSmarts("[+1!h0!$([*]~[-1,-2,-3,-4]),-1!$([*]~[+1,+2,+3,+4])]")
    at_matches = mol.GetSubstructMatches(pattern)
    at_matches_list = [y[0] for y in at_matches]
    if len(at_matches_list) > 0:
        for at_idx in at_matches_list:
            atom = mol.GetAtomWithIdx(at_idx)
            chg = atom.GetFormalCharge()
            hcount = atom.GetTotalNumHs()
            atom.SetFormalCharge(0)
            atom.SetNumExplicitHs(hcount - chg)
            atom.UpdatePropertyCache()
    return mol


def remove_stereo(smi: str):
    smi = smi.replace("/", "").replace("\\", "").replace("@", "").replace("@@", "")
    return smi


def parse_formula(formula: str) -> dict[str, float]:  # from pymatgen
    def get_sym_dict(form: str, factor) -> dict[str, float]:
        sym_dict: dict[str, float] = collections.defaultdict(float)
        for m in re.finditer(r"([A-Z][a-z]*)\s*([-*\.e\d]*)", form):
            el = m.group(1)
            amt = 1.0
            if m.group(2).strip() != "":
                amt = float(m.group(2))
            sym_dict[el] += amt * factor
            form = form.replace(m.group(), "", 1)
        if form.strip():
            raise ValueError(f"{form} is an invalid formula!")
        return sym_dict

    m = re.search(r"\(([^\(\)]+)\)\s*([\.e\d]*)", formula)
    if m:
        factor = 1.0
        if m.group(2) != "":
            factor = float(m.group(2))
        unit_sym_dict = get_sym_dict(m.group(1), factor)
        expanded_sym = "".join([f"{el}{amt}" for el, amt in unit_sym_dict.items()])
        expanded_formula = formula.replace(m.group(), expanded_sym)
        return parse_formula(expanded_formula)
    return get_sym_dict(formula, 1)


def smi2imagestr(smi: str):
    m = MolFromSmiles(smi)
    img = MolToImage(m)
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    encoded_image = base64.b64encode(buffered.getvalue())
    src_str = 'data:image/png;base64,{}'.format(encoded_image.decode())
    return src_str


def smiles_eq(smi1: str, smi2: str):
    return rdkit.Chem.CanonSmiles(remove_stereo(smi1), useChiral=0) \
           == rdkit.Chem.CanonSmiles(remove_stereo(smi2), useChiral=0)
