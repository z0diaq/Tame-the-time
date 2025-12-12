# ADR-018: Windows Installer with PyInstaller and Inno Setup

**Status**: Accepted  
**Date**: 2025-12-12  
**Deciders**: Development Team  
**Technical Story**: Windows platform distribution strategy

## Context

Tame-the-Time is a Python-based Tkinter application that previously required users to install Python and dependencies manually. Windows users need a self-contained, easy-to-install application package that:
- Does not require Python installation
- Includes all dependencies (matplotlib, PyYAML, requests, Tkinter)
- Provides standard Windows installation experience (installer wizard, desktop shortcuts, uninstaller)
- Can be built automatically in CI/CD pipeline
- Integrates with existing Poetry-based build system

## Decision

We will use **PyInstaller + Inno Setup** to create self-contained Windows installers:

1. **PyInstaller** bundles the Python application and all dependencies into a single executable
2. **Inno Setup** packages the executable into a professional Windows installer (.exe)
3. **GitHub Actions** builds Windows installers automatically on version tag pushes
4. **Poetry** manages PyInstaller as an optional build dependency

### Key Implementation Details

**PyInstaller Configuration** (`tame_the_time.spec`):
- Single-file executable mode for simplicity
- Includes all data files (locales, examples, default settings)
- Console mode disabled (GUI app only)
- Hidden imports for Tkinter, matplotlib, and other runtime dependencies

**Inno Setup Configuration** (`installer.iss`):
- Multi-language support (English, French, Spanish, Polish)
- Optional desktop icon creation
- Program Files installation directory
- Start menu shortcuts
- Professional uninstaller
- Version automatically synced from Git tags

**GitHub Actions Workflow**:
- Three-job pipeline: Python packages → Windows installer → Release creation
- Runs on `windows-latest` for Windows-specific builds
- Uses Chocolatey to install Inno Setup
- Uploads all artifacts (wheel, source, installer) to single release

**Poetry Integration**:
```toml
[tool.poetry.group.build]
optional = true

[tool.poetry.group.build.dependencies]
pyinstaller = "^6.0.0"
```

## Consequences

### Positive

1. **User Experience**: Windows users can install with one click, no Python knowledge required
2. **Professional**: Standard Windows installer experience with proper uninstaller
3. **CI/CD Integration**: Fully automated builds on tag pushes
4. **Multi-Language**: Installer supports all application languages
5. **Poetry Compatible**: Uses existing package manager, doesn't interfere with pip/wheel builds
6. **Maintainable**: Version auto-synced, no manual version updates needed
7. **Comprehensive**: All distribution formats (wheel, source, Windows installer) built together

### Negative

1. **Large File Size**: Windows installer ~50-80MB due to bundled Python runtime and dependencies
2. **Build Time**: Adds ~5-10 minutes to release pipeline (Windows runner + PyInstaller)
3. **Windows-Only Testing**: Cannot fully test Windows installer on Linux/Mac development machines
4. **Maintenance**: Two build configurations to maintain (pyinstaller.spec + installer.iss)
5. **GitHub Actions Cost**: Windows runners cost more than Linux runners

### Neutral

1. **Not MSI**: Uses .exe installer format instead of native .msi (but most users won't care)
2. **Single Architecture**: Builds for x64 only (covers 99%+ of modern Windows systems)
3. **Code Signing**: Currently not code-signed (future enhancement)

## Alternatives Considered

### cx_Freeze
- **Pros**: Native MSI support, simpler configuration
- **Cons**: Less mature Tkinter support, fewer users/documentation
- **Verdict**: Rejected due to lower confidence in Tkinter compatibility

### Nuitka
- **Pros**: Compiles to native code, faster execution, smaller size
- **Cons**: Much longer build times (20-30 min), requires C++ compiler, more complex setup
- **Verdict**: Rejected due to complexity and build time overhead

### py2exe
- **Pros**: Simple, lightweight
- **Cons**: Unmaintained since Python 3.4, no Python 3.12 support
- **Verdict**: Rejected due to lack of maintenance

### Direct Executable Distribution (no installer)
- **Pros**: Simpler, just ship .exe file
- **Cons**: No uninstaller, no Start Menu integration, poor UX
- **Verdict**: Rejected - users expect proper installers

### Manual Windows Builds
- **Pros**: No CI/CD complexity
- **Cons**: Error-prone, time-consuming, inconsistent builds
- **Verdict**: Rejected - automation is essential for reliability

## Implementation

### Build Tools
- **PyInstaller 6.0+**: Application bundler
- **Inno Setup 6**: Installer creator (installed via Chocolatey in CI)
- **Poetry**: Dependency management with optional build group

### Files Created
- `tame_the_time.spec`: PyInstaller configuration
- `installer.iss`: Inno Setup installer script
- `.github/workflows/release.yml`: Extended for Windows builds

### Build Process
1. Push version tag (e.g., `v0.2.0`)
2. GitHub Actions triggers three parallel jobs:
   - Ubuntu: Build wheel + source with Poetry
   - Windows: Build installer with PyInstaller + Inno Setup
   - (After both complete) Create release with all artifacts

### Testing Strategy
- Local testing: Run `poetry run pyinstaller tame_the_time.spec` on Windows
- CI testing: Automated verification in GitHub Actions
- Manual testing: Install on clean Windows VM after release

## References

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Inno Setup Documentation](https://jrsoftware.org/isinfo.php)
- [ADR-017: Semantic Versioning with Poetry](adr_017_semantic_versioning_poetry.md)
- [GitHub Actions: Building on Windows](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners#supported-runners-and-hardware-resources)

## Notes

- Windows installer filename format: `TameTheTime-{version}-Setup.exe`
- Installer size: ~50-80MB (includes Python 3.12 runtime + all dependencies)
- Build time: ~5-10 minutes on GitHub Actions Windows runners
- First Windows installer will be created on next version tag push
- Users can still install via pip/wheel if preferred (Python required)
