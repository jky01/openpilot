#!/usr/bin/env bash

echo "🚀 啟動性能優化的 openpilot..."

# 基本模擬環境變數
export PASSIVE="0"
export NOBOARD="1"
export SIMULATION="1"
export SKIP_FW_QUERY="1"
export FINGERPRINT="HONDA_CIVIC_2022"

# 性能優化 - 禁用更多組件以減少負載
export BLOCK="${BLOCK},camerad,loggerd,encoderd,micd,logmessaged,sensord,updated,athena"

# GPU 優化
export CUDA_VISIBLE_DEVICES=0
export __GL_SYNC_TO_VBLANK=0
export __GLX_VENDOR_LIBRARY_NAME=nvidia

# CPU 優化
export OMP_NUM_THREADS=6
export OPENBLAS_NUM_THREADS=6

# 減少日誌輸出
export PYTHONUNBUFFERED=0

# 關閉 CI 模式以啟用 UI
unset CI

echo "✅ 環境變數設置完成"
echo "🔧 設置模擬參數..."

source openpilot_venv/bin/activate
python3 -c "from openpilot.selfdrive.test.helpers import set_params_enabled; set_params_enabled()"

echo "🎯 啟動 manager..."
SCRIPT_DIR=$(dirname "$0")
OPENPILOT_DIR=$SCRIPT_DIR

cd $OPENPILOT_DIR/system/manager && exec ./manager.py
