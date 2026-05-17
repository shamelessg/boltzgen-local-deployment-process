# BOLTZGEN Local Deployment & High-Throughput Peptide Screening

基于 [BOLTZGEN](https://github.com/HannesStark/boltzgen) 分子生成模型，在 CentOS 7 服务器上完成从**环境部署 → 靶点配置 → 批量预测**的全流程 Pipeline，对 53 个候选多肽配体进行靶点结合预测筛选。

## 项目概述

BOLTZGEN 是一个基于等变扩散模型的蛋白质-配体结合分子生成框架。本项目将其部署在无 root 权限、Slurm 调度器停用的 CentOS 7 服务器上，并通过空间位点计算方法批量生成靶点配置文件，实现高通量预测。

## 技术栈

`Python` `Conda` `Docker` `Singularity` `Bash` `YAML` `OpenMM` `Linux`

## 仓库结构

```
.
├── README.md
├── configs/                    # 53 个蛋白的 YAML 靶点配置
├── scripts/
│   ├── generate_yaml.py        # 基于空间距离的批量 YAML 生成脚本
│   └── batch_run.sh            # 无调度器环境下的批量任务脚本
├── LEADS-PEP_inputfiles/       # 原始蛋白质 PDB 数据 (53 个蛋白)
├── work/                       # BOLTZGEN 运行工作目录
├── deploy/
│   └── DEPLOY.md               # 部署全流程踩坑记录 (Conda→Docker→Singularity→Venv)
└── results/                    # 模型预测结果输出
```

## 工作流

```
原始蛋白 PDB 数据
    │
    ▼
空间位点分析 (generate_yaml.py)
    │  欧氏距离计算蛋白-配体原子接触位点 (cutoff < 3.0Å)
    │  自动识别主链 & 结合热点残基
    ▼
53 个靶点 YAML 配置文件
    │
    ▼
BOLTZGEN 批量预测 (batch_run.sh)
    │  Singularity 容器 + Venv 次级环境
    │  OPENBLAS/OMP/MKL 线程控制
    ▼
每个蛋白 100 个候选分子设计 → results/
```

## 关键技术挑战与解决方案

### 1. 跨平台模型部署 — Conda → Docker → Singularity 三层迁移

| 尝试 | 方法 | 结果 | 原因 |
|------|------|------|------|
| 1 | Conda/Pip 服务器直接部署 | ❌ | CentOS 7 glibc 2.17 无法编译三角函数驱动 |
| 2 | Docker macOS 本地构建 | ⚠️ | 模型可加载，但无 GPU 直通，推理不可接受 |
| 3 | Docker → Singularity 打包迁移 | ❌ | 容器内 Python 包缓存路径冲突 |
| 4 | Singularity + Venv 次级环境 | ✅ | 在容器内创建 venv，export 到工作目录 |

### 2. 空间位点自动识别与批量配置生成

- **问题**：BOLTZGEN 需要为每个蛋白手写 YAML，指定主链 ID、结合位点残基编号、配体链 ID 和序列长度
- **方法**：解析 PDB 原子坐标 → 遍历蛋白-配体原子对 → 3.0Å 欧氏距离判定接触 → 自动提取主链热点残基 → 动态分配配体链 ID → 生成 YAML
- **验证**：先在 ViewMol 网站手动标注 1B9J 蛋白靶点，与脚本输出对比，确认一致后批量生成剩余 52 个

### 3. 无调度器环境的批量任务管理

- **问题**：服务器 Slurm 不可用，OpenMP 默认线程数导致资源竞争
- **解决**：手写 Shell 任务队列 + `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` 限制线程

## 快速复现

```bash
# 1. 准备 Singularity 镜像 (详见 deploy/DEPLOY.md)
singularity build boltzgen.sif docker-archive://boltzgen.tar

# 2. 批量生成靶点配置
python scripts/generate_yaml.py

# 3. 创建 targets.txt (每行一个蛋白名)
ls configs/ | sed 's/.yaml//' > targets.txt

# 4. 批量运行预测
bash scripts/batch_run.sh
```

## 能力映射

| 项目工作 | 体现能力 |
|---|---|
| CentOS 7 glibc 兼容性排查 | Linux 系统诊断、底层依赖分析 |
| Docker → Singularity 容器迁移 | 容器化技术、跨平台部署 |
| Venv 次级环境修复缓存冲突 | Python 环境管理、依赖隔离 |
| 空间位点方法批量生成 YAML | 计算化学背景、PDB 结构解析、Python 自动化 |
| 手写任务队列 + 线程控制 | Shell 编程、HPC 资源管理、并行调试 |
| ViewMol 手动验证 + 脚本批量处理 | 干湿实验交叉验证意识 |
| 完整部署文档 & 可复现脚本 | 科研可复现性、工程文档规范 |

## 原始项目

- [BOLTZGEN](https://github.com/HannesStark/boltzgen) — Hannes Stark et al., "BOLTZGEN: Equivariant Diffusion Models for Structure-Based Drug Design"

## 致谢

感谢 BOLTZGEN 作者开源模型权重与代码。
