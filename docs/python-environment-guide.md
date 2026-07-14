# Python Environment Guide — Raspberry Pi OS Trixie (64-bit)

> **Target:** Raspberry Pi OS Trixie (Debian 13), 64-bit  
> **Python Version:** 3.12+ (system default)  
> **Audience:** Beginners to intermediate — complete venv workflow

---

## Table of Contents

1. [System Python Overview](#system-python-overview)
2. [Why Virtual Environments?](#why-virtual-environments)
3. [Create Virtual Environment](#create-virtual-environment)
4. [Activate Virtual Environment](#activate-virtual-environment)
5. [Upgrade pip, setuptools, wheel](#upgrade-pip-setuptools-wheel)
6. [Install Project Requirements](#install-project-requirements)
7. [Common ML Libraries on Raspberry Pi](#common-ml-libraries-on-raspberry-pi)
8. [Remove / Recreate Virtual Environment](#remove--recreate-virtual-environment)
9. [Using pyenv for Multiple Python Versions](#using-pyenv-for-multiple-python-versions)
10. [Troubleshooting](#troubleshooting)
11. [Quick Reference](#quick-reference)

---

## System Python Overview

```bash
# Check system Python version
python3 --version
# Python 3.12.x (Trixie default)

# Check pip version
pip3 --version
# pip 24.x from /usr/lib/python3/dist-packages

# Check installed packages
pip3 list
```

> **Important:** Never install project packages globally with `sudo pip3 install`. Always use a virtual environment.

---

## Why Virtual Environments?

| Problem | Virtual Environment Solution |
|---------|------------------------------|
| **System package conflicts** | Isolated package namespace |
| **Different projects need different versions** | Per-project dependencies |
| **Breaking system tools (apt)** | No `sudo pip` needed |
| **Reproducible environments** | `requirements.txt` + fresh venv |
| **Easy cleanup** | `rm -rf .venv` and start over |

---

## Create Virtual Environment

### Standard Method (Recommended)

```bash
# Navigate to your project directory
cd ~/wmldad/rpi   # or wherever your project is

# Create virtual environment named .venv
python3 -m venv .venv

# Verify creation
ls -la .venv/
# Should show: bin/  lib/  lib64/  pyvenv.cfg  share/
```

> 📸 **Screenshot Placeholder:** *Terminal showing `python3 -m venv .venv` command and resulting directory structure*

### With Specific Python Version (if multiple installed)

```bash
# If you have python3.11 and python3.12
python3.11 -m venv .venv
# or
python3.12 -m venv .venv
```

### With Custom Prompt Name

```bash
python3 -m venv .venv --prompt "water-meter"
# Prompt will show: (water-meter) user@pi:~$
```

---

## Activate Virtual Environment

### Linux/macOS (bash/zsh)

```bash
# Activate
source .venv/bin/activate

# Your prompt changes to:
(.venv) pi@water-meter:~/wmldad/rpi $

# Verify
which python
# /home/pi/wmldad/rpi/.venv/bin/python

which pip
# /home/pi/wmldad/rpi/.venv/bin/pip
```

### Windows (Git Bash / WSL)

```bash
source .venv/bin/activate
```

### Windows (Command Prompt)

```cmd
.venv\Scripts\activate.bat
```

### Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
# If script execution blocked:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Deactivate

```bash
deactivate
# Prompt returns to normal
```

> 📸 **Screenshot Placeholder:** *Terminal showing activated venv with modified prompt and `which python` output*

---

## Upgrade pip, setuptools, wheel

**Always do this first in a new venv:**

```bash
# Ensure venv is activated
source .venv/bin/activate

# Upgrade core packaging tools
pip install --upgrade pip setuptools wheel

# Verify
pip --version
# pip 24.x from /home/pi/wmldad/rpi/.venv/lib/python3.12/site-packages/pip (python 3.12)
```

> **Why?** Older pip/setuptools/wheel can fail on modern packages (especially manylinux wheels, pyproject.toml builds).

---

## Install Project Requirements

### From requirements.txt

```bash
# Ensure venv is activated
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Or with verbose output
pip install -v -r requirements.txt
```

### Example requirements.txt for Water Meter Project

```text
# rpi/requirements.txt
flask>=3.0
pyrebase4>=4.5
xgboost>=2.0
scikit-learn>=1.3
pandas>=2.0
numpy>=1.24
joblib>=1.3
gunicorn>=21.0
python-dotenv>=1.0
requests>=2.31
```

### Install with Constraints (for reproducibility)

```bash
# Generate constraints from working environment
pip freeze > constraints.txt

# Later: install with exact versions
pip install -r requirements.txt -c constraints.txt
```

### Install Individual Packages

```bash
# Latest version
pip install flask

# Specific version
pip install 'xgboost==2.0.3'

# Version range
pip install 'numpy>=1.24,<2.0'

# From GitHub
pip install git+https://github.com/nhorvath/Pyrebase4.git

# With extras
pip install 'flask[cors]'
```

---

## Common ML Libraries on Raspberry Pi

### Installation Notes for ARM64 (Pi 3B+/4/5)

| Library | Install Command | Notes |
|---------|----------------|-------|
| **numpy** | `pip install numpy` | Uses OpenBLAS; ~2 min build on Pi 4 |
| **pandas** | `pip install pandas` | Depends on numpy; ~3 min |
| **scikit-learn** | `pip install scikit-learn` | Pure Python + some C; ~2 min |
| **xgboost** | `pip install xgboost` | **Pre-built wheels available for ARM64** — fast! |
| **scipy** | `pip install scipy` | Heavy build (~10 min); consider `sudo apt install python3-scipy` |
| **joblib** | `pip install joblib` | Pure Python; instant |
| **opencv-python** | `pip install opencv-python-headless` | Use `-headless` variant (no GUI deps) |
| **pillow** | `pip install pillow` | System deps: `sudo apt install libjpeg-dev zlib1g-dev` |
| **firebase-admin** | `pip install firebase-admin` | For server-side Firebase (if not using Pyrebase4) |

### System Dependencies (Install Once)

```bash
# Run ONCE on fresh Pi OS for ML builds
sudo apt update && sudo apt install -y \
    build-essential \
    cmake \
    libatlas-base-dev \
    libopenblas-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libcanberra-gtk3-module \
    python3-dev \
    pkg-config
```

> ⏱ **Time:** ~5-10 minutes on Pi 4/5

### Verify ML Stack

```bash
# Test all imports
python3 -c "
import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
import joblib
print(f'NumPy: {np.__version__}')
print(f'Pandas: {pd.__version__}')
print(f'scikit-learn: {sklearn.__version__}')
print(f'XGBoost: {xgb.__version__}')
print(f'joblib: {joblib.__version__}')
print('✅ All ML libraries loaded successfully')
"
```

> 📸 **Screenshot Placeholder:** *Terminal output showing successful import of all ML libraries with versions*

---

## Remove / Recreate Virtual Environment

### When to Recreate

- Python version changed (e.g., 3.11 → 3.12)
- `pip install` broken beyond repair
- Want completely clean slate
- Moved project to different location

### Remove

```bash
# Deactivate first
deactivate

# Remove completely
rm -rf .venv

# Verify gone
ls -la .venv 2>/dev/null || echo "Removed"
```

### Recreate

```bash
# Fresh venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

> 📸 **Screenshot Placeholder:** *Terminal sequence: deactivate → rm -rf .venv → python3 -m venv .venv → activate → pip install*

---

## Using pyenv for Multiple Python Versions

> **Only needed if** you require a specific Python version not in apt repos.

### Install pyenv

```bash
# Prerequisites
sudo apt update && sudo apt install -y \
    git curl build-essential \
    libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev \
    libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv
curl https://pyenv.run | bash

# Add to ~/.bashrc
cat >> ~/.bashrc <<'EOF'
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
eval "$(pyenv virtualenv-init -)"
EOF

# Reload shell
source ~/.bashrc
```

### Install Python Version

```bash
# List available versions
pyenv install --list | grep " 3\.1[12]\."

# Install specific version
pyenv install 3.12.4

# Set local version for project
cd ~/wmldad/rpi
pyenv local 3.12.4

# Now python3 points to 3.12.4
python3 --version
# Python 3.12.4
```

### Create Venv with pyenv Python

```bash
# Uses the pyenv-local version
python3 -m venv .venv
source .venv/bin/activate
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'venv'`

```bash
# Install venv module (should be included but sometimes missing)
sudo apt install -y python3.12-venv
# Or for generic:
sudo apt install -y python3-venv
```

### Issue: `pip install` fails with `error: subprocess-exited-with-error`

```bash
# Usually missing build dependencies
# For numpy/scipy/pandas:
sudo apt install -y build-essential libatlas-base-dev libopenblas-dev

# For pillow:
sudo apt install -y libjpeg-dev zlib1g-dev

# For opencv:
sudo apt install -y libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-glx
```

### Issue: `externally-managed-environment` error (PEP 668)

```bash
# This happens if you try pip install globally on Trixie
# Solution: USE A VIRTUAL ENVIRONMENT
python3 -m venv .venv
source .venv/bin/activate
pip install package_name
```

### Issue: `pip install xgboost` takes forever / fails

```bash
# XGBoost has ARM64 wheels — should be fast
# If building from source, need:
sudo apt install -y cmake build-essential

# Or use system package (older version):
sudo apt install -y python3-xgboost
```

### Issue: Out of Memory During pip install

```bash
# Add swap temporarily
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# After install:
sudo swapoff /swapfile
sudo rm /swapfile
```

### Issue: Permission Denied on ~/.cache/pip

```bash
# Fix ownership
sudo chown -R $USER:$USER ~/.cache/pip
```

### Issue: `ImportError: libopenblas.so.0: cannot open shared object file`

```bash
sudo apt install -y libopenblas0
# Or reinstall numpy in venv:
pip uninstall numpy && pip install numpy --no-binary :all:
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Create venv | `python3 -m venv .venv` |
| Activate (Linux/macOS) | `source .venv/bin/activate` |
| Activate (Windows CMD) | `.venv\Scripts\activate.bat` |
| Activate (Windows PS) | `.venv\Scripts\Activate.ps1` |
| Deactivate | `deactivate` |
| Upgrade pip | `pip install --upgrade pip setuptools wheel` |
| Install from requirements | `pip install -r requirements.txt` |
| Freeze requirements | `pip freeze > requirements.txt` |
| Show installed packages | `pip list` |
| Show package info | `pip show numpy` |
| Uninstall package | `pip uninstall numpy` |
| Remove venv | `deactivate && rm -rf .venv` |
| Check Python path | `which python` |
| Check pip path | `which pip` |
| Test ML imports | `python -c "import numpy, pandas, sklearn, xgboost; print('OK')"` |

---

## Project-Specific: Water Meter ML Backend

```bash
# 1. Clone repo (if not done)
git clone https://github.com/qppd/wmldad.git
cd wmldad/rpi

# 2. Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade tools
pip install --upgrade pip setuptools wheel

# 4. Install system deps for ML (run once)
sudo apt update && sudo apt install -y \
    build-essential libatlas-base-dev libopenblas-dev \
    libjpeg-dev zlib1g-dev python3-dev pkg-config

# 5. Install Python deps
pip install -r requirements.txt

# 6. Copy model files (from training)
mkdir -p models
# Copy xgboost_model.json, isolation_forest.pkl, scaler.pkl to models/

# 7. Copy Firebase config
cp firebase_config.json.example firebase_config.json
# Edit with your credentials

# 8. Set environment variables
export FIREBASE_EMAIL="esp32@your-project.iam.gserviceaccount.com"
export FIREBASE_PASSWORD="your-password"
export DEVICE_ID="wm_001"

# 9. Run
python app.py

# 10. For production: set up systemd service (see rpi-backend.md)
```

---

## Official References

- [Python venv Documentation](https://docs.python.org/3/library/venv.html)
- [pip User Guide](https://pip.pypa.io/en/stable/user_guide/)
- [Raspberry Pi Python Documentation](https://www.raspberrypi.com/documentation/computers/os.html#python)
- [XGBoost Installation Guide](https://xgboost.readthedocs.io/en/stable/install.html)
- [scikit-learn Installation](https://scikit-learn.org/stable/install.html)
- [NumPy on Raspberry Pi](https://numpy.org/doc/stable/user/building.html#building-on-raspberry-pi)
- [Debian Python Policy (PEP 668)](https://www.python.org/dev/peps/pep-0668/)

---

## Next Steps

Proceed to:
1. [Arduino IDE Installation Guide](./arduino-ide-installation.md) — GUI method for ESP32 firmware
2. [ESP32 Setup Guide](./esp32-setup-guide.md) — Board manager, drivers, upload
3. [Project Setup Guide](./setup.md) — Full deployment

---

*Last updated: July 2026 | Tested on Raspberry Pi OS Trixie (64-bit) with Python 3.12 | Compatible with Pi 3B+/4/5*