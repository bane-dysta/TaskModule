# test_smiles_parser.py
import smiles_parser

def test_smiles_to_geometry():
    # 定义测试的 SMILES 字符串，例如乙醇 CCO
    smiles = "CCO"
    
    # 调用 smiles_to_geometry 函数
    try:
        result = smiles_parser.smiles_to_geometry(smiles)
        print("Geometry data:", result["geometry"])
        print("Charge:", result["charge"])
        print("Spin multiplicity:", result["spin_multiplicity"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_smiles_to_geometry()
