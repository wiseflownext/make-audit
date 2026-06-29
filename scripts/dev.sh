#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5174}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "==> HR 审核资料生成器 — 本地开发启动"
echo "    项目目录: $ROOT"
echo

# ── Backend ────────────────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ 未找到 python3，请先安装 Python ≥ 3.11" >&2
  exit 1
fi

if [[ ! -d "$ROOT/backend/.venv" ]]; then
  echo "==> 创建 Python 虚拟环境…"
  python3 -m venv "$ROOT/backend/.venv"
fi

# shellcheck disable=SC1091
source "$ROOT/backend/.venv/bin/activate"

if ! python -c "import uvicorn" 2>/dev/null; then
  echo "==> 安装后端依赖…"
  pip install -q -r "$ROOT/backend/requirements.txt"
fi

if lsof -ti:"$BACKEND_PORT" >/dev/null 2>&1; then
  echo "⚠  端口 $BACKEND_PORT 已被占用，跳过后端启动（假定已在运行）"
else
  echo "==> 启动后端 http://127.0.0.1:$BACKEND_PORT"
  (
    cd "$ROOT/backend"
    exec uvicorn app.main:app --reload --port "$BACKEND_PORT"
  ) &
  BACKEND_PID=$!

  for _ in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
      echo "✓ 后端就绪"
      break
    fi
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
      echo "✗ 后端启动失败，请检查上方错误日志" >&2
      exit 1
    fi
    sleep 0.2
  done

  if ! curl -sf "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
    echo "✗ 后端在 6 秒内未响应 /health" >&2
    exit 1
  fi
fi

# ── Frontend ───────────────────────────────────────────────────────────────
if ! command -v npm >/dev/null 2>&1; then
  echo "✗ 未找到 npm，请先安装 Node.js ≥ 18" >&2
  exit 1
fi

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "==> 安装前端依赖…"
  (cd "$ROOT/frontend" && npm install)
fi

if lsof -ti:"$FRONTEND_PORT" >/dev/null 2>&1; then
  echo "⚠  端口 $FRONTEND_PORT 已被占用"
  echo "    若前端已在运行，请直接访问: http://localhost:$FRONTEND_PORT/"
  echo "    若要重启，请先结束占用该端口的进程"
  exit 1
fi

echo "==> 启动前端 http://localhost:$FRONTEND_PORT/"
echo "    按 Ctrl+C 停止（会同时关闭本脚本启动的后端）"
echo

cd "$ROOT/frontend"
exec npm run dev -- --port "$FRONTEND_PORT"
