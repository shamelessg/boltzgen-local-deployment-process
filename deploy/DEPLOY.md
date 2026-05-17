# BOLTZGEN 部署记录

## 目标环境

- **OS**: CentOS 7 (glibc 2.17, kernel 3.10)
- **GPU**: NVIDIA A100 × 4 (CUDA 11.8)
- **限制**: 无 root 权限、Slurm 调度器关闭、无 Docker

## 尝试 1: Conda/Pip 直接部署 (失败)

```bash
conda create -n boltzgen python=3.9
conda activate boltzgen
pip install boltzgen  # 或从源码安装
```

**报错**:
```
ImportError: /lib64/libm.so.6: version `GLIBC_2.27' not found
```

**根因**: BOLTZGEN 依赖的某些数值计算库需要 glibc ≥ 2.27，CentOS 7 仅提供 2.17。

**决策**: 放弃裸机 Python 环境，转向容器化。

## 尝试 2: Docker macOS 本地构建 (部分成功)

```bash
# 在 macOS (Apple Silicon) 上构建
docker build -t boltzgen:latest .
docker run --gpus all boltzgen:latest python -c "import boltzgen"
```

**结果**: 模型加载成功，参数可正常读取。但：
- macOS 无 NVIDIA GPU 直通，推理速度极慢（预计单蛋白需数小时）
- Docker 镜像无法直接在 CentOS 7 上运行（Docker 未安装且无 root）

**决策**: 本地构建 Docker 镜像 → 导出 tar → 服务器 Singularity 导入。

## 尝试 3: Docker → Singularity 跨平台迁移

```bash
# 本地：导出 Docker 镜像
docker save boltzgen:latest -o boltzgen.tar

# 上传到服务器
scp boltzgen.tar chenxq@server:/home/chenxq/boltzgen_me/

# 服务器：构建 Singularity 镜像
module load singularity
singularity build boltzgen.sif docker-archive://boltzgen.tar
```

**新问题**: Singularity 容器的只读文件系统导致 BOLTZGEN 在运行时尝试写入缓存路径失败：
```
PermissionError: [Errno 13] Permission denied: '/.cache/torch/...'
```

## 尝试 4: Venv 次级环境修复 (成功)

在容器内创建 venv，并将缓存路径重定向到可写的工作目录：

```bash
# 在容器内创建 Python venv
singularity exec boltzgen.sif python -m venv boltz_env

# 安装 BOLTZGEN 到 venv
singularity exec boltzgen.sif bash -c "source ./boltz_env/bin/activate && pip install boltzgen"

# 设置 HuggingFace 镜像 & 缓存路径
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=$(pwd)/cache

# 运行
singularity exec --nv boltzgen.sif \
  bash -c "source ./boltz_env/bin/activate && boltzgen run config.yml ..."
```

**成功**。至此模型可在服务器正常推理。

## 线程控制

OpenMP/OpenBLAS/MKL 默认使用所有 CPU 核心，在多任务并行时造成资源竞争：

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

强制单线程消除竞争，由 Shell 脚本逐任务串行调度。

## 最终部署命令

```bash
module load singularity
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=$(pwd)/cache
export CUDA_VISIBLE_DEVICES=4
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

singularity exec --nv boltzgen.sif \
  bash -c "source ./boltz_env/bin/activate && boltzgen run work/<PROTEIN>/<PROTEIN>.yaml \
    --output work/<PROTEIN>/result_100 \
    --num_designs 100 \
    --protocol protein-anything \
    --diffusion_batch_size 2"
```
