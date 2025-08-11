# GitHub crawler

## Setup env

### Install python3.11+ and venv (or similar) if not installed to create virtual environment

**Create virtual envirinment:**
```bash
python3 -m venv venv
```

**Activate venv:**
```bash
. ./venv/bin/activate
```

**Install requirements:**
```bash
pip install -r requirements.txt
```

## Usage


**Configure proxies or leave empty to use your IP directly**
> settings.py

**Run crawler:**
```bash
python run.py
```

See results in `results/` folder


# Code quality

**Run pre-commit:**
```bash
python pre-commit run
```

**Run pytest coverage:**
```bash
pytest --cov
```
