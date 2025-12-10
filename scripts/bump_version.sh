#!/bin/bash
# Helper script to bump version and keep files in sync
# Usage: ./scripts/bump_version.sh [patch|minor|major]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if argument provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No version bump type specified${NC}"
    echo "Usage: $0 [patch|minor|major|prerelease]"
    echo ""
    echo "Examples:"
    echo "  $0 patch      # 0.1.0 → 0.1.1 (bug fixes)"
    echo "  $0 minor      # 0.1.0 → 0.2.0 (new features)"
    echo "  $0 major      # 0.9.0 → 1.0.0 (breaking changes)"
    echo "  $0 prerelease # 0.1.0 → 0.1.1-alpha.0"
    exit 1
fi

BUMP_TYPE=$1

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(patch|minor|major|prerelease|prepatch|preminor|premajor)$ ]]; then
    echo -e "${RED}Error: Invalid bump type '$BUMP_TYPE'${NC}"
    echo "Valid types: patch, minor, major, prerelease, prepatch, preminor, premajor"
    exit 1
fi

echo -e "${YELLOW}Bumping version: $BUMP_TYPE${NC}"
echo ""

# Get current version
CURRENT_VERSION=$(poetry version -s)
echo "Current version: $CURRENT_VERSION"

# Bump version in pyproject.toml
poetry version $BUMP_TYPE

# Get new version
NEW_VERSION=$(poetry version -s)
echo -e "${GREEN}New version: $NEW_VERSION${NC}"
echo ""

# Update __version__.py
echo "Updating __version__.py..."
cat > __version__.py << EOF
"""Version information for Tame-the-Time application."""

__version__ = "$NEW_VERSION"
EOF

# Verify sync
PYPROJECT_VERSION=$(poetry version -s)
VERSION_PY=$(python3 -c "from __version__ import __version__; print(__version__)")

if [ "$PYPROJECT_VERSION" != "$VERSION_PY" ]; then
    echo -e "${RED}Error: Version mismatch after update!${NC}"
    echo "pyproject.toml: $PYPROJECT_VERSION"
    echo "__version__.py: $VERSION_PY"
    exit 1
fi

echo -e "${GREEN}✓ Version files synchronized${NC}"
echo ""

# Update README.md version
if [ -f "README.md" ]; then
    echo "Updating README.md..."
    sed -i "s/\*\*Version:\*\* [0-9.]*/\*\*Version:\*\* $NEW_VERSION/" README.md
    echo -e "${GREEN}✓ README.md updated${NC}"
fi

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review changes:"
echo "   git diff pyproject.toml __version__.py README.md"
echo ""
echo "2. Update CHANGELOG.md with release notes"
echo ""
echo "3. Commit changes:"
echo "   git add pyproject.toml __version__.py README.md CHANGELOG.md"
echo "   git commit -m \"chore: bump version to $NEW_VERSION\""
echo ""
echo "4. Create and push tag:"
echo "   git tag -a \"v$NEW_VERSION\" -m \"Release version $NEW_VERSION\""
echo "   git push origin main"
echo "   git push origin \"v$NEW_VERSION\""
echo ""
echo -e "${GREEN}GitHub Actions will automatically build and release!${NC}"
