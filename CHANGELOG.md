# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.1.4] - 2025-12-18

### Changes
- New release to verify GitHub Actions release workflow

## [0.1.3] - 2025-12-16

### Changes
- New release to verify GitHub Actions release workflow

## [0.1.2] - 2025-12-14

### Added
- Windows installer build with PyInstaller and Inno Setup
- Self-contained Windows executable (no Python installation required)
- Professional Windows installer with multi-language support (EN, FR, ES, PL)
- Automated Windows installer builds in GitHub Actions release workflow
- PyInstaller as optional build dependency in Poetry

### Changed
- Extended GitHub Actions release workflow to build Windows installers alongside Python packages
- Release artifacts now include wheel, source, and Windows installer

### Fixed
- Python version constraint to <3.15 for PyInstaller compatibility

### Documentation
- ADR-018: Windows Installer with PyInstaller and Inno Setup
- Updated RELEASE_PROCESS.md with Windows build information

## [0.1.1] - 2025-12-11

### Added
- GitHub Actions workflow for automated releases
- Poetry-based distribution packaging
- Helper script for version bumping (`scripts/bump_version.sh`)

### Changed
- Migrated to Poetry for dependency management
- Added `requests` dependency for Gotify notifications

### Fixed
- Version consistency between `pyproject.toml` and `__version__.py`

## [0.1.0] - 2025-12-08

### Added
- Initial release with semantic versioning
- Timeboxing timeline with visual cards
- Task tracking and completion status
- Statistics and charts (daily, weekly, monthly, yearly)
- Internationalization support (English, French, Spanish, Polish)
- Day rollover functionality with schedule switching
- Gotify notification integration
- Interactive card repositioning
- URL extraction from tasks
- Forgiving streak counting
- SQLite-based task tracking database
- YAML-based schedule configuration
- Multiple schedule support (per-day templates)
- Global options dialog for configuration
- Command-line arguments for testing and simulation
- Example schedules (software engineer, college student, ADHD structure)

### Technical Features
- Layered architecture with separation of concerns
- Service layer pattern for business logic
- Dependency injection for testability
- Canvas-based timeline rendering
- Event-driven UI architecture
- Configuration management with user settings persistence

[Unreleased]: https://github.com/z0diaq/Tame-the-time/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/z0diaq/Tame-the-time/releases/tag/v0.1.0
