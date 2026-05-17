#!/bin/bash

GPU_ID=4                
BATCH_SIZE=2            
NUM_DESIGNS=100         
TARGET_LIST="targets.txt" 

module load singularity
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=$(pwd)/cache

export CUDA_VISIBLE_DEVICES=$GPU_ID

export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "🚀 炼丹炉启动！正在使用 GPU $GPU_ID"

for TARGET in $(cat $TARGET_LIST); do
    echo "[$(date '+%H:%M:%S')] 正在处理蛋白: $TARGET"

    
    singularity exec --nv boltzgen.sif \
      bash -c "source ./boltz_env/bin/activate && boltzgen run work/${TARGET}/${TARGET}.yaml \
        --output work/${TARGET}/result_100 \
        --num_designs $NUM_DESIGNS \
        --protocol protein-anything \
        --diffusion_batch_size $BATCH_SIZE"

    if [ $? -eq 0 ]; then
        echo "✅ $TARGET 完成"
    else
        echo "❌ $TARGET 失败，请检查日志"
    fi
done

echo "🎉 所有任务执行完毕！"
