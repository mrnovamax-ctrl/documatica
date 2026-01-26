#!/bin/bash
# Copilot Skills Pack Installer
# Устанавливает набор AI-скиллов для VS Code Copilot
set -e

SKILLS_DIR=".github/skills"
mkdir -p "$SKILLS_DIR"

echo "======================================"
echo "  Copilot Skills Pack Installer"
echo "======================================"
echo ""

# v12-style (Documatica Design System)
if [ ! -d "$SKILLS_DIR/v12-style" ]; then
  echo "[1/6] Installing v12-style (Design System)..."
  git clone --depth 1 --quiet https://github.com/mrnovamax-ctrl/documatica-v12-skill.git /tmp/v12-skill 2>/dev/null || true
  if [ -d "/tmp/v12-skill" ]; then
    cp -r /tmp/v12-skill "$SKILLS_DIR/v12-style"
    rm -rf /tmp/v12-skill
    echo "      Done!"
  else
    echo "      Skipped (repo not available)"
  fi
else
  echo "[1/6] v12-style already installed"
fi

# Clone awesome-copilot once
echo "[2/6] Fetching awesome-copilot repository..."
rm -rf /tmp/awesome-copilot
git clone --depth 1 --quiet https://github.com/github/awesome-copilot.git /tmp/awesome-copilot

# git-commit
if [ ! -d "$SKILLS_DIR/git-commit" ]; then
  echo "[3/6] Installing git-commit (Conventional Commits)..."
  cp -r /tmp/awesome-copilot/skills/git-commit "$SKILLS_DIR/"
  echo "      Done!"
else
  echo "[3/6] git-commit already installed"
fi

# refactor
if [ ! -d "$SKILLS_DIR/refactor" ]; then
  echo "[4/6] Installing refactor (Code Improvement)..."
  cp -r /tmp/awesome-copilot/skills/refactor "$SKILLS_DIR/"
  echo "      Done!"
else
  echo "[4/6] refactor already installed"
fi

# prd
if [ ! -d "$SKILLS_DIR/prd" ]; then
  echo "[5/6] Installing prd (Product Requirements)..."
  cp -r /tmp/awesome-copilot/skills/prd "$SKILLS_DIR/"
  echo "      Done!"
else
  echo "[5/6] prd already installed"
fi

# webapp-testing
if [ ! -d "$SKILLS_DIR/webapp-testing" ]; then
  echo "[6/6] Installing webapp-testing (Playwright)..."
  cp -r /tmp/awesome-copilot/skills/webapp-testing "$SKILLS_DIR/"
  echo "      Done!"
else
  echo "[6/6] webapp-testing already installed"
fi

# web-design-reviewer
if [ ! -d "$SKILLS_DIR/web-design-reviewer" ]; then
  echo "[7/6] Installing web-design-reviewer..."
  cp -r /tmp/awesome-copilot/skills/web-design-reviewer "$SKILLS_DIR/"
  echo "      Done!"
else
  echo "[7/6] web-design-reviewer already installed"
fi

# Cleanup
rm -rf /tmp/awesome-copilot

echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "Installed skills:"
ls -1 "$SKILLS_DIR" | grep -v README
echo ""
echo "Restart VS Code to activate skills."
