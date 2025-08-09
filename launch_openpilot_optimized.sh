#!/usr/bin/env bash

# 優化的 openpilot 模擬啟動腳本
echo "啟動優化的 openpilot 模擬環境..."

# 基本模擬環境變數
export PASSIVE="0"
export NOBOARD="1"
export SIMULATION="1"
export SKIP_FW_QUERY="1"
export FINGERPRINT="HONDA_CIVIC_2022"

# 優化設置 - 禁用不必要的組件以提高性能
export BLOCK="${BLOCK},camerad,loggerd,encoderd,micd,logmessaged,sensord,updated"

# GPU 加速設置
export CUDA_VISIBLE_DEVICES=0
export __GL_SYNC_TO_VBLANK=0

# 性能調優
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4

# 減少日誌輸出
export PYTHONUNBUFFERED=0

echo "設置模擬參數..."
source openpilot_venv/bin/activate
python3 -c "from openpilot.selfdrive.test.helpers import set_params_enabled; set_params_enabled()"

echo "啟動 manager..."
SCRIPT_DIR=$(dirname "$0")
OPENPILOT_DIR=$SCRIPT_DIR

cd $OPENPILOT_DIR/system/manager && exec ./manager.py
