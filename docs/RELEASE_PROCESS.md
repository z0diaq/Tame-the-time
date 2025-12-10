# Release Process with GitHub Actions

This guide explains how to create releases using the automated GitHub Actions workflow.

## Overview

When you push a version tag (e.g., `v0.1.0`) to GitHub, the following happens automatically:

1. ✅ GitHub Actions triggers the build workflow
2. 🔨 Poetry builds distribution packages (wheel + source)
3. 📦 Creates a GitHub Release with the packages attached
4. 📝 Generates release notes from commits
5. 🎯 Marks pre-releases (alpha/beta/rc) appropriately

## Prerequisites

- Repository must be pushed to GitHub
- GitHub Actions must be enabled (enabled by default)
- You must have write access to the repository

## Quick Release Process

### 1. Update Version

```bash
# For a bug fix (0.1.0 → 0.1.1)
poetry version patch

# For a new feature (0.1.0 → 0.2.0)
poetry version minor

# For breaking changes (0.9.0 → 1.0.0)
poetry version major
```

### 2. Update __version__.py

**IMPORTANT:** Keep `__version__.py` in sync with `pyproject.toml`:

```bash
# Get current version from Poetry
VERSION=$(poetry version -s)

# Update __version__.py
echo "\"\"\"Version information for Tame-the-Time application.\"\"\"

__version__ = \"$VERSION\"" > __version__.py
```

Or manually edit `__version__.py`:
```python
__version__ = "0.2.0"  # Match pyproject.toml
```

### 3. Update CHANGELOG (Recommended)

Create or update `CHANGELOG.md`:

```markdown
## [0.2.0] - 2025-12-10

### Added
- New feature X
- New feature Y

### Changed
- Improved performance of Z

### Fixed
- Fixed bug in W
```

### 4. Commit Changes

```bash
git add pyproject.toml __version__.py CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
```

### 5. Create and Push Tag

```bash
# Get version from Poetry
VERSION=$(poetry version -s)

# Create annotated tag
git tag -a "v${VERSION}" -m "Release version ${VERSION}"

# Push commits and tag
git push origin main
git push origin "v${VERSION}"
```

### 6. Monitor GitHub Actions

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Watch the "Build and Release" workflow run
4. Wait for completion (usually 2-3 minutes)

### 7. Verify Release

1. Go to **Releases** tab on GitHub
2. Verify the new release is created
3. Check that both files are attached:
   - `tame_the_time-0.2.0-py3-none-any.whl`
   - `tame_the_time-0.2.0.tar.gz`

## Manual Release (Fallback)

If GitHub Actions fails or you need to create a release manually:

### 1. Build Locally

```bash
poetry build
```

### 2. Create Release on GitHub

1. Go to repository → **Releases** → **Draft a new release**
2. Choose tag: Select existing tag or create new one
3. Release title: `Release v0.2.0`
4. Upload files from `dist/`:
   - `tame_the_time-0.2.0-py3-none-any.whl`
   - `tame_the_time-0.2.0.tar.gz`
5. Write release notes
6. Click **Publish release**

## Pre-release Versions

For alpha, beta, or release candidate versions:

```bash
# Create pre-release version
poetry version prerelease  # 0.1.0 → 0.1.1a0

# Or set specific pre-release
poetry version 0.2.0-beta.1
```

GitHub Actions automatically marks releases as "pre-release" if the version contains:
- `alpha` (e.g., v0.2.0-alpha.1)
- `beta` (e.g., v0.2.0-beta.1)
- `rc` (e.g., v0.2.0-rc.1)

## Automated Workflow Details

### Trigger Condition

The workflow triggers on tags matching the pattern `v*.*.*`:
- ✅ `v0.1.0` - triggers
- ✅ `v1.2.3` - triggers
- ✅ `v0.2.0-beta.1` - triggers
- ❌ `0.1.0` - does NOT trigger (missing 'v' prefix)
- ❌ `release-0.1.0` - does NOT trigger (wrong format)

### What Gets Built

The workflow:
1. Checks out the tagged commit
2. Sets up Python 3.12
3. Installs Poetry
4. Installs dependencies via `poetry install`
5. Builds packages via `poetry build`
6. Creates GitHub Release
7. Uploads both `.whl` and `.tar.gz` files

### Release Assets

Each release includes:
- **Wheel package** (`.whl`) - Binary distribution for fast installation
- **Source package** (`.tar.gz`) - Source distribution for pip/Poetry

### Release Notes

Release notes are auto-generated from:
- Commit messages since last tag
- Pull request titles
- Contributor list

You can manually edit release notes after creation.

## Troubleshooting

### Workflow Fails to Trigger

**Problem:** Pushed tag but no workflow runs

**Solutions:**
- Ensure tag follows `v*.*.*` pattern (e.g., `v0.1.0`, not `0.1.0`)
- Check GitHub Actions is enabled: Settings → Actions → General
- Verify workflow file exists at `.github/workflows/release.yml`

### Version Mismatch Error

**Problem:** Workflow fails with version mismatch

**Solution:** Ensure `pyproject.toml` and `__version__.py` have the same version:

```bash
# Check versions
poetry version -s
python -c "from __version__ import __version__; print(__version__)"

# Fix mismatch - update __version__.py to match pyproject.toml
```

### Build Fails

**Problem:** `poetry build` fails in workflow

**Common causes:**
- Missing dependency in `pyproject.toml`
- Syntax error in Python files
- Missing required files specified in `include`

**Solution:** Test build locally first:
```bash
poetry build
```

### Release Creation Fails

**Problem:** Workflow completes but no release created

**Solutions:**
- Check GitHub token permissions
- Verify `GITHUB_TOKEN` has write access
- Repository settings → Actions → General → Workflow permissions → "Read and write permissions"

### Wrong Files Attached

**Problem:** Release doesn't have the right files

**Solution:** The workflow expects these exact filenames:
- `dist/tame_the_time-{VERSION}-py3-none-any.whl`
- `dist/tame_the_time-{VERSION}.tar.gz`

Verify Poetry builds with correct naming.

## Testing Before Release

Before pushing a tag, validate everything works:

```bash
# 1. Update version
poetry version patch

# 2. Update __version__.py to match
# (edit manually or use script above)

# 3. Test build locally
poetry build

# 4. Test installation
pip install dist/*.whl
tame-the-time --version
pip uninstall tame-the-time -y

# 5. Clean up
rm -rf dist/

# 6. Commit and tag
git add pyproject.toml __version__.py
git commit -m "chore: bump version to X.Y.Z"
git tag -a "vX.Y.Z" -m "Release version X.Y.Z"
git push origin main
git push origin vX.Y.Z
```

## Rollback a Release

If you need to delete a release:

### Delete Release on GitHub
1. Go to Releases
2. Click the release
3. Click "Delete release"

### Delete Tag
```bash
# Delete local tag
git tag -d v0.2.0

# Delete remote tag
git push origin :refs/tags/v0.2.0
```

## Best Practices

1. **Always test locally** before pushing tag
2. **Keep version consistency** between `pyproject.toml` and `__version__.py`
3. **Write meaningful release notes** - edit auto-generated notes
4. **Use semantic versioning** - follow MAJOR.MINOR.PATCH strictly
5. **Tag from main branch** - ensure stable code
6. **Update CHANGELOG** before each release
7. **Test installation** from built packages before releasing

## CI/CD Status Badges

Add to README.md to show build status:

```markdown
![Build and Release](https://github.com/z0diaq/Tame-the-time/actions/workflows/release.yml/badge.svg)
![Test Build](https://github.com/z0diaq/Tame-the-time/actions/workflows/test.yml/badge.svg)
```

## Future Enhancements

Consider adding:
- **PyPI publishing** - Automatically upload to PyPI
- **Automated testing** - Run tests before building
- **Code signing** - Sign release packages
- **Docker images** - Build and publish Docker containers
- **Checksums** - Generate SHA256 checksums for downloads

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Semantic Versioning](https://semver.org/)
- [docs/VersionUpdate.md](VersionUpdate.md) - Detailed versioning guide
