#!/bin/bash

set -e  # 一旦出错就退出

echo "Building project..."
npm run build

echo "Moving exported static files..."

TARGET_DIR="../server/static/out"

# 删除旧的目标目录
if [ -d "$TARGET_DIR" ]; then
  echo "Removing old static files..."
  rm -rf "$TARGET_DIR"
fi

mv out "$TARGET_DIR"
echo "Done! Static site is in $TARGET_DIR"
