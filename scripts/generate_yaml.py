import os
import math
import shutil

# 定义路径
leads_pep_dir = r'c:\Users\wrcccc\Desktop\LEADS-PEP_inputfiles'
output_dir = r'c:\Users\wrcccc\Desktop\work'
CUTOFF_DIST = 3.0  # 结合热点的判定距离：小于3.0埃

# 创建输出目录
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def parse_pdb(filepath):
    """简易 PDB 解析器，提取原子坐标和氨基酸残基数量"""
    atoms = []
    res_ids = set()
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith("ATOM  ") or line.startswith("HETATM"):
                chain = line[21].strip()
                if not chain: chain = 'A' # 容错处理
                res_id = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                atoms.append({'chain': chain, 'res_id': res_id, 'x': x, 'y': y, 'z': z})
                res_ids.add(res_id)
    return atoms, len(res_ids)

# 遍历LEADS-PEP_inputfiles目录下的所有文件夹
for protein_dir in os.listdir(leads_pep_dir):
    protein_path = os.path.join(leads_pep_dir, protein_dir)
    
    # 只处理目录
    if not os.path.isdir(protein_path):
        continue
    
    # 检查是否存在clean_protein.pdb和clean_ligand.pdb文件
    clean_protein_file = os.path.join(protein_path, f'{protein_dir}_clean_protein.pdb')
    clean_ligand_file = os.path.join(protein_path, f'{protein_dir}_clean_ligand.pdb')
    
    if not (os.path.exists(clean_protein_file) and os.path.exists(clean_ligand_file)):
        print(f'Skipping {protein_dir} - missing clean files')
        continue
    
    print(f'正在深度扫描并计算 {protein_dir} 的结合位点...')
    # 解析PDB文件
    prot_atoms, _ = parse_pdb(clean_protein_file)
    lig_atoms, lig_length = parse_pdb(clean_ligand_file)
    
    # 暴力计算距离（空间坐标欧氏距离）
    interacting_res = set()
    for p in prot_atoms:
        for l in lig_atoms:
            dist = math.sqrt((p['x']-l['x'])**2 + (p['y']-l['y'])**2 + (p['z']-l['z'])**2)
            if dist < CUTOFF_DIST:
                interacting_res.add((p['chain'], p['res_id']))
                break # 这个蛋白原子已经确认接触了，直接测下一个
    
    # 整理结果，找出主链
    chain_dict = {}
    for chain, res_id in interacting_res:
        chain_dict.setdefault(chain, []).append(res_id)
    
    if not chain_dict:
        print(f'警告：{protein_dir} 没有找到接触点！')
        continue
    
    main_chain = max(chain_dict, key=lambda k: len(chain_dict[k]))
    hotspots = ",".join(map(str, sorted(list(set(chain_dict[main_chain])))))
    
    # 动态分配配体的 ID，防止与主链 ID 发生同名冲突
    ligand_id = 'C' if main_chain.upper() == 'B' else 'B'
    
    # 创建蛋白质文件夹
    protein_output_dir = os.path.join(output_dir, protein_dir)
    if not os.path.exists(protein_output_dir):
        os.makedirs(protein_output_dir)
    
    # 生成yaml文件内容
    yaml_content = f"""entities:
  - file:
      path: /home/chenxq/boltzgen_me/LEADS-PEP_inputfiles/{protein_dir}/{protein_dir}_clean_protein.pdb
      include:
        - chain:
            id: {main_chain}
      binding_types:
        - chain:
            id: {main_chain}
            binding: {hotspots}

  - protein:
      id: {ligand_id}
      sequence: {lig_length}
"""
    
    # 保存yaml文件
    output_file = os.path.join(protein_output_dir, f'{protein_dir}.yaml')
    with open(output_file, 'w') as f:
        f.write(yaml_content)
    
    print(f'Generated {output_file}')

print('\n全部搞定！所有文件夹和完美 YAML 配置已生成！')