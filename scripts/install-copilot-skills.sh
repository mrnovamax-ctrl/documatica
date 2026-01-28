#!/bin/bash
# Copilot Skills Pack Installer
# Устанавливает набор AI-скиллов для VS Code Copilot
# 
# Использование:
#   curl -sSL https://raw.githubusercontent.com/mrnovamax-ctrl/copilot-skills-pack/main/install.sh | bash
#
set -e

SKILLS_DIR=".github/skills"
REPO_URL="https://github.com/mrnovamax-ctrl/copilot-skills-pack.git"

echo "======================================"
echo "  Copilot Skills Pack Installer"
echo "======================================"
echo ""
echo "Skills included:"
echo "  - v12-style (Design System, 50+ components)"
echo "  - git-commit (Conventional Commits)"
echo "  - refactor (Code Improvement)"
echo "  - prd (Product Requirements)"
echo "  - webapp-testing (Playwright)"
echo "  - web-design-reviewer (Design Review)"
echo ""

# Clone the pack
echo "[1/2] Downloading skills pack..."
rm -rf /tmp/copilot-skills-pack
git clone --depth 1 --quiet "$REPO_URL" /tmp/copilot-skills-pack

# Copy skills
echo "[2/2] Installing skills..."
mkdir -p "$SKILLS_DIR"

for skill in git-commit prd refactor v12-style webapp-testing web-design-reviewer; do
  if [ -d "/tmp/copilot-skills-pack/$skill" ]; then
    cp -r "/tmp/copilot-skills-pack/$skill" "$SKILLS_DIR/"
    echo "      + $skill"
  fi
done

# Copy README
cp /tmp/copilot-skills-pack/README.md "$SKILLS_DIR/" 2>/dev/null || true

# Cleanup
rm -rf /tmp/copilot-skills-pack

echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "Installed skills:"
ls -1 "$SKILLS_DIR" | grep -v README
echo ""
echo "Restart VS Code to activate skills."
