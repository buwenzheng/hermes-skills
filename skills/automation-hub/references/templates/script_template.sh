#!/bin/bash
# ============================================================
# 自动化脚本模板
# 使用说明：
#   1. 复制此模板到 ~/.hermes/scripts/automation/{任务名}.sh
#   2. 修改 CONFIG 区域的变量
#   3. 实现 main 逻辑
#   4. 用 chmod +x 赋予执行权限
#   5. cronjob 创建时 script 指向此文件
# ============================================================

set -euo pipefail

# ---- CONFIG ----
# TASK_NAME="signin_xxx"
# LOG_DIR="$HOME/.hermes/logs/automation"
# PROXY_ENV="http://127.0.0.1:7890"

# ---- INIT ----
# mkdir -p "$LOG_DIR"

# ---- MAIN ----
# 在这里写你的逻辑
# echo "任务执行成功"    # 有输出 = 推送消息
# (无输出 = 静默，不推送)

# ---- PROXY HELPER ----
# 如需代理：
# export http_proxy="$PROXY_ENV"
# export https_proxy="$PROXY_ENV"
# ... 执行网络请求 ...
# unset http_proxy https_proxy
