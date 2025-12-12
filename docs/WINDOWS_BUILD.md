# Windows Installer Build Guide

This guide explains how to build the Windows installer locally or understand the automated CI/CD process.

## Overview

The Windows installer is built using:
- **PyInstaller**: Bundles Python app + dependencies into single executable
- **Inno Setup**: Creates professional Windows installer (.exe)
- **GitHub Actions**: Automates builds on version tag pushes

## Prerequisites

### For Local Builds (Windows Only)

1. **Python 3.12+** installed
2. **Poetry** installed (`pip install poetry`)
3. **Inno Setup 6** installed:
   - Download from: https://jrsoftware.org/isdl.php
   - Or via Chocolatey: `choco install innosetup`

### For Understanding CI/CD (Any Platform)

No local build environment needed - GitHub Actions handles everything automatically.

## Automated Builds (GitHub Actions)

### How It Works

When you push a version tag (e.g., `v0.2.0`), GitHub Actions automatically:

1. **Builds Python packages** on Ubuntu:
   - Wheel package (`.whl`)
   - Source distribution (`.tar.gz`)

2. **Builds Windows installer** on Windows runner:
   - Installs Poetry and dependencies
   - Runs PyInstaller to create executable
   - Installs Inno Setup via Chocolatey
   - Creates Windows installer

3. **Creates GitHub Release**:
   - Downloads all build artifacts
   - Creates release with all files attached
   - Generates release notes

### Workflow File

Located at: `.github/workflows/release.yml`

Key jobs:
- `build-python-packages`: Builds wheel and source on Ubuntu
- `build-windows-installer`: Builds Windows installer on Windows
- `create-release`: Combines all artifacts into GitHub release

### Triggering a Build

```bash
# Push version tag
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0

# Monitor at: https://github.com/z0diaq/Tame-the-time/actions
```

## Local Build (Windows)

### Step 1: Install Dependencies

```bash
# Install all dependencies including build tools
poetry install --with build
```

This installs PyInstaller and other optional build dependencies.

### Step 2: Build Executable with PyInstaller

```bash
# Build using the spec file
poetry run pyinstaller tame_the_time.spec
```

**Expected output:**
- Executable: `dist/TameTheTime.exe` (~60-80MB)
- Build logs in `build/` directory

**Verify executable:**
```bash
# Test the executable
.\dist\TameTheTime.exe --version
```

### Step 3: Create Installer with Inno Setup

```bash
# Run Inno Setup compiler (adjust path if needed)
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

**Expected output:**
- Installer: `dist/installer/TameTheTime-0.1.1-Setup.exe`

**Verify installer:**
- Run the installer on a clean Windows VM
- Install to Program Files
- Check Start Menu shortcuts
- Test uninstaller

## Configuration Files

### tame_the_time.spec (PyInstaller)

Defines how the executable is built:

```python
a = Analysis(
    ['TameTheTime.py'],              # Entry point
    datas=[                          # Data files to include
        ('locales', 'locales'),
        ('examples', 'examples'),
        ('default_settings.yaml', '.'),
    ],
    hiddenimports=[                  # Runtime imports
        'tkinter',
        'matplotlib',
        'yaml',
    ],
)
```

**Key settings:**
- `console=False`: No console window (GUI only)
- `upx=True`: Compress executable
- Single-file mode: All in one `.exe`

### installer.iss (Inno Setup)

Defines installer behavior:

```iss
#define MyAppVersion "0.1.1"
DefaultDirName={autopf}\{#MyAppName}
OutputDir=dist\installer
```

**Key features:**
- Multi-language support (EN, FR, ES, PL)
- Desktop icon (optional)
- Start Menu shortcuts
- Uninstaller registration

**Version management:**
- Version is auto-updated in CI/CD from Git tags
- For local builds, manually edit `MyAppVersion` line

## Troubleshooting

### PyInstaller Errors

**Problem:** `ModuleNotFoundError` when running executable

**Solution:** Add missing module to `hiddenimports` in `tame_the_time.spec`:
```python
hiddenimports=[
    'tkinter',
    'your_missing_module',
],
```

**Problem:** Data files not found (locales, examples)

**Solution:** Verify `datas` list in spec file includes all required directories.

### Inno Setup Errors

**Problem:** `ISCC.exe` not found

**Solution:** Install Inno Setup or adjust path in build command.

**Problem:** Version mismatch in installer filename

**Solution:** Update `MyAppVersion` in `installer.iss` to match `pyproject.toml`.

### Large Executable Size

**Expected:** 60-80MB (includes Python runtime, Tkinter, matplotlib, etc.)

To reduce size:
1. Enable UPX compression (`upx=True` in spec)
2. Exclude unnecessary modules in `excludes` list
3. Consider using onedir mode instead of onefile (trade-off: multiple files)

### Antivirus False Positives

PyInstaller executables sometimes trigger antivirus warnings.

**Solutions:**
- Code signing (future enhancement)
- Submit to antivirus vendors for whitelisting
- Use official GitHub releases (better reputation)

## File Sizes

| Artifact | Size |
|----------|------|
| TameTheTime.exe (executable) | ~60-80MB |
| Installer (TameTheTime-X.Y.Z-Setup.exe) | ~50-80MB |
| Wheel package (.whl) | ~100KB |
| Source package (.tar.gz) | ~80KB |

Windows installer is large because it includes:
- Python 3.12 runtime
- Tkinter
- matplotlib
- All dependencies
- Localization files

## Testing Checklist

Before releasing Windows installer:

- [ ] Executable runs without errors
- [ ] `--version` flag works
- [ ] All UI elements display correctly
- [ ] Localization works (EN, FR, ES, PL)
- [ ] Settings persist across restarts
- [ ] Database creation/access works
- [ ] Gotify notifications work (if configured)
- [ ] Charts render correctly (matplotlib)
- [ ] Installer creates shortcuts
- [ ] Uninstaller removes all files
- [ ] No antivirus false positives

## CI/CD Build Time

Typical GitHub Actions workflow duration:
- Python packages: ~2 minutes
- Windows installer: ~5-10 minutes
- Total (including release): ~12-15 minutes

Windows builds take longer due to:
- Windows runner startup
- Chocolatey package installation
- PyInstaller bundling process

## Future Enhancements

Potential improvements:

1. **Code Signing**: Sign executable with certificate
2. **Auto-update**: Built-in update checker
3. **MSI Format**: Create native MSI installer (via WiX or cx_Freeze)
4. **Portable Version**: Standalone executable without installer
5. **Size Optimization**: Further reduce executable size
6. **Multi-architecture**: ARM64 support for Windows on ARM

## References

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [ADR-018: Windows Installer Decision](adr/adr_018_windows_installer_pyinstaller.md)
- [Release Process](RELEASE_PROCESS.md)

## Support

For issues with Windows builds:
- Check GitHub Actions logs for CI/CD failures
- Verify Python 3.12 compatibility
- Test on clean Windows 10/11 VM
- Report issues at: https://github.com/z0diaq/Tame-the-time/issues
