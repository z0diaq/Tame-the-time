# Installation Guide for End Users

This guide explains how to install Tame-the-Time on your system.

## Prerequisites

- Python 3.12 or higher
- pip (Python package installer)

## Installation Methods

### Method 1: Install from Distribution Package (Recommended)

If you have received a `.whl` (wheel) or `.tar.gz` file:

```bash
# Install from wheel file
pip install tame_the_time-0.1.0-py3-none-any.whl

# OR install from source distribution
pip install tame_the_time-0.1.0.tar.gz
```

After installation, you can run the application with:

```bash
tame-the-time
```

Or with Python module syntax:

```bash
python -m tame_the_time
```

### Method 2: Install from PyPI (Future)

Once published to PyPI, you'll be able to install with:

```bash
pip install tame-the-time
```

### Method 3: Install from Source

For developers or if you want to modify the code:

1. Clone the repository:
   ```bash
   git clone https://github.com/z0diaq/Tame-the-time.git
   cd Tame-the-time
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run directly:
   ```bash
   python3 TameTheTime.py
   ```

### Method 4: Development Installation with Poetry

For contributors and developers:

1. Install Poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Clone and install:
   ```bash
   git clone https://github.com/z0diaq/Tame-the-time.git
   cd Tame-the-time
   poetry install
   ```

3. Run with Poetry:
   ```bash
   poetry run tame-the-time
   ```

## Verify Installation

Check the installed version:

```bash
tame-the-time --version
```

Should output:
```
Tame-the-Time version 0.1.0
```

## Uninstallation

To remove the application:

```bash
pip uninstall tame-the-time
```

## Troubleshooting

### "command not found: tame-the-time"

If you get this error, the Python scripts directory is not in your PATH.

**Solution 1:** Use the module syntax instead:
```bash
python -m tame_the_time
```

**Solution 2:** Add Python scripts directory to PATH:

On Linux/Mac:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add this line to your `~/.bashrc` or `~/.zshrc` to make it permanent.

On Windows:
```cmd
set PATH=%PATH%;%APPDATA%\Python\Python312\Scripts
```

### Missing Dependencies

If you get import errors, ensure all dependencies are installed:

```bash
pip install matplotlib PyYAML requests
```

### Permission Errors

If you get permission errors during installation, try:

```bash
# Install for current user only
pip install --user tame_the_time-0.1.0-py3-none-any.whl
```

## Next Steps

After installation:

1. Run the application: `tame-the-time`
2. Load an example schedule: File → Open → Select an example YAML file
3. Customize your schedule: Right-click on cards to edit
4. Check the [README.md](../README.md) for more features and usage examples

## System Requirements

- **OS:** Linux, macOS, Windows (with tkinter support)
- **Python:** 3.12 or higher
- **RAM:** Minimum 512 MB
- **Storage:** ~50 MB for application and dependencies
- **Display:** GUI environment with tkinter support

## Getting Help

- **Issues:** https://github.com/z0diaq/Tame-the-time/issues
- **Documentation:** See `docs/` directory
- **Examples:** See `examples/` directory for sample schedules
