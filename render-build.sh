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

  # Prefer npm ci if lockfile exists (faster & reproducible)
  if [ -f "package-lock.json" ]; then
    echo "📦 Installing node dependencies via npm ci"
    npm ci
  else
    echo "📦 Installing node dependencies via npm install"
    npm install
  fi

  echo "🏗️ Running frontend build..."
  npm run build

  # --- Ensure correct output folder ---
  # If React default build folder exists but dist does not, rename it
  if [ -d "build" ] && [ ! -d "dist" ]; then
    echo "🔄 Renaming React build folder → dist/"
    mv build dist
  fi

  popd >/dev/null
  echo "✅ Frontend build complete (webapp/dist)"
else
  echo "⚠️ webapp/ folder not found. Skipping frontend build."
fi

echo "✅ Build phase complete."
