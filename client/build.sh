#!/bin/bash
# BuildH得到HTML和资源文件存放在/server/static/out/subsystem/qa_out下
set -e
echo "Building project..."
npm run build
mv out qa_out
echo "Moving exported static files..."
TARGET_DIR="../server/static/subsystem/qa_out"

if [ -d "$TARGET_DIR" ]; then
  echo "Removing old static files..."
  rm -rf "$TARGET_DIR"
  mkdir -p "$TARGET_DIR"
else
  echo "Target Folder Do Not Exist, Creating..."
  mkdir -p "$TARGET_DIR"
fi

mv qa_out/* "$TARGET_DIR"
rmdir qa_out
echo "Done! Static site is in $TARGET_DIR"
