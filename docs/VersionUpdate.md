# Version Update Guide

This guide explains how to properly update the version number for Tame-the-Time when releasing new changes.

## Semantic Versioning Overview

Tame-the-Time follows [Semantic Versioning 2.0.0](https://semver.org/):

**Version Format: MAJOR.MINOR.PATCH** (e.g., 0.1.0, 1.2.3, 2.0.0)

- **MAJOR**: Incompatible API changes or major architectural shifts
- **MINOR**: New features added in backward-compatible manner  
- **PATCH**: Backward-compatible bug fixes

### Pre-1.0.0 Versions (Initial Development)

During initial development (0.x.y versions), the following rules apply:
- **0.MINOR.PATCH**: Breaking changes are allowed in MINOR versions
- Signals to users that the API is not yet stable
- Rapid iteration and experimentation are expected
- Version 1.0.0 indicates the first stable public API

---

## Quick Start with Helper Script

**The easiest way to bump version:**

```bash
# For bug fixes
./scripts/bump_version.sh patch

# For new features
./scripts/bump_version.sh minor

# For breaking changes
./scripts/bump_version.sh major
```

This script automatically:
- Updates version in `pyproject.toml`
- Syncs version in `__version__.py`
- Updates version in `README.md`
- Verifies consistency
- Shows you the next steps

---

## Quick Decision Guide

**Ask yourself: What type of changes am I releasing?**

### Bug Fixes Only → PATCH Release
```bash
poetry version patch
# Example: 0.1.0 → 0.1.1
```

**Examples:**
- Fixed crash when loading invalid schedule file
- Corrected time calculation in statistics dialog
- Fixed UI rendering issue on specific screen sizes
- Resolved memory leak in canvas rendering
- Fixed translation typo in French locale

---

### New Features (Backward Compatible) → MINOR Release
```bash
poetry version minor
# Example: 0.1.0 → 0.2.0
```

**Examples:**
- Added new chart type to statistics dialog
- Implemented export functionality for task data
- Added keyboard shortcuts for common actions
- Introduced new configuration option with sensible default
- Added support for new language (e.g., German)
- Enhanced existing feature without breaking current usage

---

### Breaking Changes → MAJOR Release
```bash
poetry version major
# Example: 0.9.0 → 1.0.0
```

**Examples (Pre-1.0.0):**
- Restructured configuration file format (YAML keys changed)
- Changed database schema requiring migration
- Removed deprecated command-line arguments
- Changed public API for extension developers

**Examples (Post-1.0.0):**
- Same as above, with more caution and migration guides
- Removed features that users rely on
- Changed behavior of existing features in incompatible way

---

## Step-by-Step Release Process

### 1. Determine Version Bump Type

Review your changes and decide: PATCH, MINOR, or MAJOR?

```bash
# Review recent changes
git log --oneline v0.1.0..HEAD

# Check modified files
git diff v0.1.0..HEAD --name-only
```

### 2. Update Version with Poetry

```bash
# For bug fixes
poetry version patch

# For new features
poetry version minor

# For breaking changes
poetry version major
```

This command updates the version in `pyproject.toml` automatically.

### 3. Update CHANGELOG (If Exists)

Create or update `CHANGELOG.md` with the new version and changes:

```markdown
## [0.2.0] - 2025-12-08

### Added
- New weekly view in statistics dialog
- German language support

### Changed
- Improved performance of timeline rendering

### Fixed
- Fixed crash when closing statistics dialog
```

### 4. Commit Version Bump

```bash
# Stage the version change
git add pyproject.toml CHANGELOG.md

# Commit with conventional format
git commit -m "feat: bump version to 0.2.0"
# or
git commit -m "fix: bump version to 0.1.1"
```

### 5. Create Git Tag

```bash
# Create annotated tag with version
poetry version --short  # Shows current version
VERSION=$(poetry version --short)
git tag -a "v${VERSION}" -m "Release version ${VERSION}"

# Example:
# git tag -a "v0.2.0" -m "Release version 0.2.0"
```

### 6. Push Changes and Tag

```bash
# Push commits
git push origin main

# Push the tag
git push origin v0.2.0
```

### 7. Build Distribution Package

```bash
# Build wheel and source distribution
poetry build

# Output: dist/tame_the_time-0.2.0.tar.gz (source)
#         dist/tame_the_time-0.2.0-py3-none-any.whl (wheel)
```

**Distribution files can be shared with end users for installation:**
```bash
# Users can install with:
pip install dist/tame_the_time-0.2.0-py3-none-any.whl
```

See [INSTALLATION.md](INSTALLATION.md) for end-user installation instructions.

---

## Special Version Commands

### Pre-release Versions

For alpha, beta, or release candidate versions:

```bash
# Create alpha pre-release (0.1.0 → 0.1.1-alpha.0)
poetry version prerelease

# Create beta pre-release
poetry version prerelease
# Manually edit to change "alpha" to "beta" in pyproject.toml

# Increment pre-release number (0.1.1-alpha.0 → 0.1.1-alpha.1)
poetry version prerelease
```

### Reset Pre-release to Release

```bash
# From 0.1.1-alpha.0 to 0.1.1
poetry version patch
```

### Check Current Version

```bash
# Show current version
poetry version

# Show just the version number
poetry version --short
```

---

## Version History Planning (Roadmap)

### Development Phase (0.x.y)
- **0.1.x**: Core timeboxing features (current)
- **0.2.x**: Gamification features (streaks, achievements)
- **0.3.x**: Advanced scheduling (recurring tasks, templates)
- **0.4.x**: Data export and reporting
- **0.5.x**: Plugin system foundation
- **0.9.x**: Stabilization and polish for 1.0.0

### Stable Release (1.0.0+)
- **1.0.0**: First stable release with backward compatibility guarantee
- **1.x.y**: New features with backward compatibility
- **2.0.0**: Major architecture changes (if needed)

---

## Common Scenarios

### Scenario 1: Fixed a Bug

```bash
# You fixed a crash in the statistics dialog
poetry version patch     # 0.1.0 → 0.1.1
git add pyproject.toml
git commit -m "fix: prevent crash when no tasks exist in statistics dialog"
git tag -a "v0.1.1" -m "Release version 0.1.1"
git push origin main
git push origin v0.1.1
```

### Scenario 2: Added New Feature

```bash
# You added a new export to CSV feature
poetry version minor     # 0.1.1 → 0.2.0
git add pyproject.toml
git commit -m "feat: add CSV export for task statistics"
git tag -a "v0.2.0" -m "Release version 0.2.0"
git push origin main
git push origin v0.2.0
```

### Scenario 3: Breaking Configuration Change

```bash
# You changed YAML configuration structure
poetry version major     # 0.9.0 → 1.0.0
# Update migration guide in docs/
git add pyproject.toml docs/MIGRATION_v1.md
git commit -m "feat!: restructure YAML configuration format

BREAKING CHANGE: Configuration file format has changed.
See docs/MIGRATION_v1.md for migration guide."
git tag -a "v1.0.0" -m "Release version 1.0.0"
git push origin main
git push origin v1.0.0
```

### Scenario 4: Multiple Changes

If your release includes multiple types of changes, use the **highest precedence**:

- Breaking changes → MAJOR (even if you also have new features and bug fixes)
- New features → MINOR (even if you also have bug fixes)
- Only bug fixes → PATCH

---

## Rollback a Version

If you made a mistake and need to rollback:

```bash
# Edit pyproject.toml manually to previous version
# Or use Poetry to set specific version:
poetry version 0.1.0

# Delete the incorrect tag
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0

# Amend or revert the commit
git revert HEAD
```

---

## Automation (Future Enhancement)

Consider adding GitHub Actions or pre-commit hooks to:
- Automatically update CHANGELOG.md from commit messages
- Validate version number format
- Ensure version is bumped before merging to main
- Auto-generate release notes from commits

---

## Questions?

- **When to release 1.0.0?** When the API is stable and you commit to backward compatibility
- **Can I skip versions?** Yes, but it's uncommon. Use if project was abandoned and resumed.
- **What about hotfixes?** Create from the release tag, bump PATCH, merge back to main
- **Pre-release naming?** Use alpha, beta, rc (release candidate) conventionally

---

## References

- [Semantic Versioning Specification](https://semver.org/)
- [Poetry Version Command Documentation](https://python-poetry.org/docs/cli/#version)
- [Conventional Commits](https://www.conventionalcommits.org/) (for commit messages)
- [Keep a Changelog](https://keepachangelog.com/) (for CHANGELOG format)
