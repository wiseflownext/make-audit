#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-18104}"
WEB_ROOT="/var/www/make-audit"
NGINX_CONF="/etc/nginx/conf.d/audit.conf"
SERVICE_NAME="make-audit-backend"

echo "==> HR 审核资料生成器 — 生产部署"
echo "    仓库: $REPO_ROOT"
echo "    后端端口: $BACKEND_PORT"
echo

cd "$REPO_ROOT"
git pull --ff-only

echo "==> 安装后端依赖"
if [[ ! -d backend/.venv ]]; then
  python3 -m venv backend/.venv
fi
# shellcheck disable=SC1091
source backend/.venv/bin/activate
pip install -q -U pip
pip install -q -r backend/requirements.txt
python -m playwright install chromium 2>/dev/null || true

echo "==> 构建前端"
cd frontend
npm ci --silent
npm run build
rsync -a --delete dist/ "$WEB_ROOT/"
cd "$REPO_ROOT"

echo "==> 配置 systemd 服务"
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=HR Audit Document Generator (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${REPO_ROOT}/backend
Environment=PATH=${REPO_ROOT}/backend/.venv/bin:/usr/local/bin:/usr/bin
ExecStart=${REPO_ROOT}/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port ${BACKEND_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo "==> 配置 Nginx"
install -m 644 "$REPO_ROOT/infra/prod/nginx/audit.conf" "$NGINX_CONF"
nginx -t
systemctl reload nginx

echo "==> 健康检查"
for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null; then
    echo "✓ 后端就绪"
    break
  fi
  sleep 1
done
curl -sf "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null || {
  echo "✗ 后端健康检查失败" >&2
  journalctl -u "${SERVICE_NAME}" -n 30 --no-pager
  exit 1
}

echo
echo "✓ 部署完成"
echo "  访问: https://audit.wiseflownext.com/"
