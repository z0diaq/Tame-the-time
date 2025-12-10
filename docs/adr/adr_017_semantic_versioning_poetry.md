Title: Semantic Versioning with Poetry for Dependency Management
Status: Accepted
Context: The Tame-the-Time application has been growing in features and complexity, with ongoing development adding new functionality regularly. As the application matures, there is a need for proper version management to communicate changes to users and maintain consistency across releases. Additionally, the current dependency management approach using a minimal requirements.txt file lacks the structure needed for proper development workflows, including development dependencies, optional features, and automated dependency resolution. The project needs a robust versioning strategy and dependency management tool that supports modern Python development practices while remaining maintainable for a single-developer project.

Decision: Implement Semantic Versioning (SemVer 2.0.0) with Poetry as the dependency management tool:

**Semantic Versioning Structure:**
- Version format: MAJOR.MINOR.PATCH (e.g., 0.1.0, 1.0.0, 2.3.1)
- MAJOR version: Incompatible API changes or major architectural shifts
- MINOR version: New features added in backward-compatible manner
- PATCH version: Backward-compatible bug fixes
- Pre-1.0.0 versions indicate initial development phase

**Poetry Integration:**
- Replace requirements.txt with pyproject.toml as single source of truth
- Use Poetry for dependency management, version updates, and package building
- Store version number in pyproject.toml [tool.poetry] section
- Separate production and development dependencies
- Define package metadata (name, description, authors, license)
- Configure project entry points for executable installation

**Initial Version:**
- Start at 0.1.0 to indicate early development stage
- Reflects stable core functionality with ongoing feature development
- Signals to users that breaking changes may occur before 1.0.0

**Version Management Workflow:**
- Use `poetry version` command for consistent version updates
- Document version update procedures in VersionUpdate.md
- Update CHANGELOG with version-specific changes
- Tag releases in Git with version numbers (v0.1.0, v1.0.0, etc.)

Consequences:

Positive:
- Clear communication of change impact through version numbers (MAJOR.MINOR.PATCH)
- Users can quickly understand the significance of updates
- Poetry provides deterministic dependency resolution via poetry.lock
- Separation of production and development dependencies reduces deployment size
- Built-in virtual environment management simplifies development setup
- Single configuration file (pyproject.toml) follows modern Python standards (PEP 518)
- Automated dependency version constraints reduce compatibility issues
- Simple version bumping with `poetry version patch/minor/major`
- Native support for building distribution packages (wheel, sdist)
- Better documentation of project metadata in standardized format
- Prepares project for potential PyPI publication in the future
- Enables reproducible builds across different environments

Negative:
- Adds Poetry as a development dependency (users must install Poetry)
- Slightly steeper learning curve compared to pip + requirements.txt
- Requires consistent discipline in following SemVer rules
- Poetry adds some overhead for simple dependency changes
- Migration from requirements.txt requires initial setup effort
- Pre-1.0.0 versions allow breaking changes, requiring careful communication
- poetry.lock file must be managed in version control (adds file size)
- Contributors need to understand Poetry workflow in addition to Git

Trade-offs:
- Increased complexity in tooling for improved dependency management
- Short-term migration effort for long-term maintainability benefits
- Standardized approach may feel restrictive but ensures consistency

Alternatives:

1. **pip + requirements.txt (current approach)**
   - Pros: Simple, minimal tooling, widely understood
   - Cons: No dependency resolution, no dev/prod separation, manual version management
   - Rejected: Insufficient for growing project complexity

2. **pipenv**
   - Pros: Dependency resolution, Pipfile format, virtual environment management
   - Cons: Slower performance, less active maintenance, no PEP 518 support
   - Rejected: Poetry has better community adoption and performance

3. **Setuptools with setup.py**
   - Pros: Traditional Python packaging, widely supported
   - Cons: More boilerplate, less modern, no built-in dependency resolution
   - Rejected: Outdated approach, superseded by pyproject.toml standard

4. **Conda**
   - Pros: Cross-language support, comprehensive package management
   - Cons: Overkill for Python-only project, larger footprint, separate ecosystem
   - Rejected: Unnecessary complexity for this project's scope

5. **Manual versioning without SemVer**
   - Pros: Complete flexibility, no rules to follow
   - Cons: No clear communication of change impact, user confusion
   - Rejected: Lack of standardization hinders user understanding

6. **Calendar Versioning (CalVer)**
   - Pros: Clear temporal context (e.g., 2024.12.1)
   - Cons: No information about change impact, not suitable for feature-driven development
   - Rejected: SemVer better fits the project's development model

Implementation Notes:

**Migration Steps:**
1. Create pyproject.toml with current dependencies from requirements.txt
2. Set initial version to 0.1.0
3. Create tame_the_time/ package directory for Poetry compatibility
4. Add __init__.py and __main__.py entry points to package
5. Configure packages and include sections in pyproject.toml
6. Add missing dependency (requests) discovered during testing
7. Run `poetry install` to generate poetry.lock
8. Add poetry.lock to version control
9. Update documentation to reflect Poetry usage
10. Keep requirements.txt in sync for backward compatibility

**Version Update Commands:**
```bash
# Patch release (0.1.0 → 0.1.1) - bug fixes
poetry version patch

# Minor release (0.1.0 → 0.2.0) - new features
poetry version minor

# Major release (0.9.0 → 1.0.0) - breaking changes
poetry version major

# Pre-release versions
poetry version prerelease  # 0.1.0 → 0.1.1-alpha.0
poetry version prepatch    # 0.1.0 → 0.1.1-alpha.0
poetry version preminor    # 0.1.0 → 0.2.0-alpha.0
poetry version premajor    # 0.1.0 → 1.0.0-alpha.0
```

**pyproject.toml Structure:**
- [tool.poetry]: Core project metadata and version
- [tool.poetry.dependencies]: Production dependencies (matplotlib, PyYAML, requests)
- [tool.poetry.group.dev.dependencies]: Development-only dependencies (pytest, pytest-cov)
- [tool.poetry.scripts]: Executable entry points (tame-the-time command)
- packages: List of Python packages to include in distribution
- include: List of data files (locales, examples, config files)
- [build-system]: Build tool configuration (Poetry Core)

**Package Structure:**
- tame_the_time/: Minimal package directory for Poetry compatibility
  - __init__.py: Package initialization with version import
  - __main__.py: Entry point wrapper that calls TameTheTime.main()
- TameTheTime.py: Main application script (kept at root for backward compatibility)
- ui/, utils/, models/, services/, config/: Application modules
- locales/: Translation files (JSON)
- examples/: Sample schedule files and screenshots
- default_settings.yaml: Default configuration template

**Version Numbering During Development (Pre-1.0.0):**
- 0.1.x: Initial stable features (day rollover, statistics, internationalization)
- 0.2.x: Gamification features (streaks, achievements)
- 0.3.x: Advanced scheduling features
- 0.x.y: Continue until API is stable and ready for 1.0.0
- 1.0.0: First stable release with commitment to backward compatibility

**Backward Compatibility:**
- Keep requirements.txt in sync initially for users without Poetry
- Document both installation methods in README
- Provide migration guide for existing users
- Can eventually deprecate requirements.txt after Poetry adoption

**Automated Release Pipeline:**
GitHub Actions workflows for CI/CD:
- **release.yml**: Triggered on version tags (v*.*.*), builds packages, creates GitHub Release
- **test.yml**: Triggered on pushes to main/develop, runs tests and validates build
- Automated version consistency checking between pyproject.toml and __version__.py
- Distribution packages automatically attached to GitHub Releases
- Helper script (scripts/bump_version.sh) automates version bumping workflow
- Pre-release detection based on version string (alpha, beta, rc markers)

**Tooling:**
- scripts/bump_version.sh: Automated version update with consistency checking
- CHANGELOG.md: Standardized changelog following Keep a Changelog format
- docs/RELEASE_PROCESS.md: Comprehensive release workflow documentation
- docs/INSTALLATION.md: End-user installation guide for distribution packages
