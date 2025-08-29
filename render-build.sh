#!/usr/bin/env bash
# render-build.sh
set -euo pipefail

echo "🔧 Using Python: $(python --version || true)"
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

echo "📚 Installing Python requirements..."
pip install -r requirements.txt

# --- Build the React/Vite WebApp ---
if [ -d "webapp" ]; then
  echo "🌐 Found webapp/ folder. Building frontend..."

  pushd webapp >/dev/null

  # Ensure Node.js version (Render default is fine, but you can pin via .nvmrc or package.json engines)
  echo "🟢 Using Node: $(node --version)"
  echo "🟢 Using NPM: $(npm --version)"

  # Prefer npm ci if lockfile exists (faster & reproducible)
  if [ -f "package-lock.json" ]; then
    echo "📦 Installing node dependencies via npm ci"
    npm ci --silent
  else
    echo "📦 Installing node dependencies via npm install"
    npm install --silent
  fi

  echo "🏗️ Running frontend build..."
  npm run build

  # --- Ensure correct output folder ---
  if [ -d "build" ] && [ ! -d "dist" ]; then
    echo "🔄 Renaming React build folder → dist/"
    mv build dist
  fi

  echo "📦 Contents of dist/:"
  ls -lah dist || true

  popd >/dev/null
  echo "✅ Frontend build complete (webapp/dist)"
else
  echo "⚠️ webapp/ folder not found. Skipping frontend build."
fi

echo "✅ Build phase complete."
