#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================"
echo " Xteink-Fontbuilder-mac - セットアップ"
echo "================================================"

if ! command -v python3 &>/dev/null; then
    echo "❌ Python3が見つかりません。https://www.python.org/downloads/ からインストールしてください。"
    exit 1
fi
echo "✅ Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")') を検出"

if [ ! -d ".venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv .venv
fi

echo "📦 依存パッケージをインストール中..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install PySide6 Pillow --quiet

echo ""
echo "================================================"
echo " セットアップ完了！"
echo " 起動: ./run.sh  または  Xteink-Fontbuilder-mac.command をダブルクリック"
echo "================================================"
