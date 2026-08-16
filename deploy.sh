#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-$VENV_DIR/bin/python}"
PIP_BIN="${PIP_BIN:-$VENV_DIR/bin/pip}"
SERVICE_NAME="${SERVICE_NAME:-calculadora-placas}"
APP_USER="${APP_USER:-www-data}"
APP_GROUP="${APP_GROUP:-www-data}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-main}"

echo "==> Projeto: $PROJECT_DIR"

if [[ ! -d "$PROJECT_DIR/.git" ]]; then
    echo "Erro: $PROJECT_DIR nao parece ser um repositorio Git."
    exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Erro: Python do ambiente virtual nao encontrado em $PYTHON_BIN"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "Erro: execute este script como root para ajustar permissoes e reiniciar o servico."
    exit 1
fi

if ! git config --global --get-all safe.directory | grep -Fxq "$PROJECT_DIR"; then
    echo "==> Registrando repositorio como safe.directory para o usuario atual"
    git config --global --add safe.directory "$PROJECT_DIR"
fi

echo "==> Atualizando codigo"
git -C "$PROJECT_DIR" fetch "$GIT_REMOTE"
git -C "$PROJECT_DIR" pull --ff-only "$GIT_REMOTE" "$GIT_BRANCH"

echo "==> Instalando dependencias"
"$PIP_BIN" install -r "$PROJECT_DIR/requirements.txt"

echo "==> Aplicando migrations"
"$PYTHON_BIN" "$PROJECT_DIR/manage.py" migrate

echo "==> Coletando arquivos estaticos"
"$PYTHON_BIN" "$PROJECT_DIR/manage.py" collectstatic --noinput

echo "==> Ajustando permissoes do SQLite e do diretorio do projeto"
if [[ -f "$PROJECT_DIR/db.sqlite3" ]]; then
    chown "$APP_USER:$APP_GROUP" "$PROJECT_DIR/db.sqlite3"
    chmod 664 "$PROJECT_DIR/db.sqlite3"
fi

chown "$APP_USER:$APP_GROUP" "$PROJECT_DIR"
chmod 775 "$PROJECT_DIR"

if [[ -d "$PROJECT_DIR/staticfiles" ]]; then
    chown -R "$APP_USER:$APP_GROUP" "$PROJECT_DIR/staticfiles"
    find "$PROJECT_DIR/staticfiles" -type d -exec chmod 755 {} \;
    find "$PROJECT_DIR/staticfiles" -type f -exec chmod 644 {} \;
fi

echo "==> Reiniciando servico $SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager

echo
echo "Deploy concluido com sucesso."
echo "Observacao: este script nao executa seed_catalogo para nao sobrescrever dados do admin."
