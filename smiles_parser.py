import re
import requests
from rdkit import Chem
from rdkit.Chem import AllChem

# A utility function to convert atomic number to element symbol using RDKit
def get_element_symbol(atomic_num):
    return Chem.GetPeriodicTable().GetElementSymbol(atomic_num)

# A utility function to calculate the formal charge of the molecule
def get_molecule_charge(mol):
    total_charge = 0
    for atom in mol.GetAtoms():
        total_charge += atom.GetFormalCharge()  # Sum up formal charges of each atom
    return total_charge

# 判断输入是否是 CAS 号
def is_cas_number(string):
    """
    Check if the input string is in CAS number format: XXXX-XX-X.
    """
    cas_regex = r'^\d{2,7}-\d{2}-\d$'
    return bool(re.match(cas_regex, string))

# 通过 CAS 号获取 SMILES 字符串
def get_smiles_from_cas(cas_number):
    """
    Fetch SMILES from PubChem using CAS number.
    """
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas_number}/property/CanonicalSMILES/JSON"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        try:
            smiles = data['PropertyTable']['Properties'][0]['CanonicalSMILES']
            return smiles
        except KeyError:
            raise ValueError(f"SMILES not found for CAS number: {cas_number}")
    else:
        raise ValueError(f"Unable to fetch data for CAS number: {cas_number}")

# 主函数：将 SMILES 或 CAS 号转化为 3D 几何结构
def smiles_to_geometry(input_string):
    """
    Convert a SMILES string or CAS number into 3D geometry, charge, and spin multiplicity.
    Returns a dictionary with the atomic coordinates, charge, and spin multiplicity.
    """
    # 如果输入是 CAS 号，先将其转换为 SMILES
    if is_cas_number(input_string):
        smiles = get_smiles_from_cas(input_string)
        print(f"CAS number {input_string} converted to SMILES: {smiles}")
    else:
        smiles = input_string
    
    # Create a molecule object from the SMILES string
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES string")
    
    # Add hydrogen atoms to the molecule
    mol = Chem.AddHs(mol)
    
    # Generate 3D coordinates
    AllChem.EmbedMolecule(mol, randomSeed=42)  # Fixed seed for reproducibility
    
    # Try to optimize the molecule using MMFF94 force field first
    try:
        mmff_props = AllChem.MMFFGetMoleculeProperties(mol, mmffVariant="MMFF94")
        if mmff_props is None:
            raise ValueError("MMFF94 parameters are not available for this molecule.")
        
        converged = AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)  # Try MMFF94 optimization
        if not converged:
            print("Warning: MMFF94 optimization did not converge within the limit.")
    except Exception as e:
        print(f"MMFF94 optimization failed: {e}. Switching to UFF force field.")
        
        # Fall back to UFF optimization if MMFF94 is not available
        converged = AllChem.UFFOptimizeMolecule(mol, maxIters=1000)
        if not converged:
            print("Warning: UFF optimization did not converge within the limit.")
    
    # Get the total charge of the molecule
    charge = get_molecule_charge(mol)
    
    # Set default spin multiplicity (assuming all closed-shell singlets unless otherwise specified)
    spin_multiplicity = 1
    
    # Extract 3D coordinates and element symbols
    atom_info = []
    conf = mol.GetConformer()
    for atom in mol.GetAtoms():
        atomic_num = atom.GetAtomicNum()
        element_symbol = get_element_symbol(atomic_num)
        pos = conf.GetAtomPosition(atom.GetIdx())
        atom_info.append(f"{element_symbol} {pos.x: .6f} {pos.y: .6f} {pos.z: .6f}")
    
    return {
        "charge": charge,
        "spin_multiplicity": spin_multiplicity,
        "geometry": atom_info
    }
