[![Tests](https://github.com/CrafterKolyan/localhost-throttle/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/CrafterKolyan/localhost-throttle/actions/workflows/tests.yml)

# localhost-throttle
Tool to throttle or redirect your network connections

## Usage
```
localhost-throttle --server <server-address> --new-server <new-server-address> --protocols tcp,udp --bandwidth <bandwidth>
```

You should think about `localhost-throttle` as a wrapper around your server.<br>
`server-address` means the original address on which the original server listens. Example: `localhost:8000`<br>
`new-server-address` means the address to which `localhost-throttle` server will be binded. Example: `0.0.0.0:8001`<br>

## Example:
```
localhost-throttle --server localhost:8000 --new-server 0.0.0.0:8001 --protocols tcp --bandwidth 100000
```

## Current features
- Redirection of TCP/UDP traffic from one port to another
- Basic TCP/UDP traffic bandwidth limitting (will be improved in the future)

## Installing package
```
pip install .
```

### Requirements
- Python 3.10+
- `setuptools>=42`
- `pip>=19`
- OS that supports threads

## Development
### Setting up environment
```
python -m venv .venv
.venv\Scripts\activate.bat  (for Windows)
.venv/Scripts/activate      (for Unix)
pip install -U setuptools
python -m pip install -U pip
pip install -r requirements-dev.txt
```

### Enabling environment
```
.venv\Scripts\activate.bat  (for Windows)
.venv/Scripts/activate      (for Unix)
```


### Running tests
```
pytest test -n auto --capture=no
```
or<br>
In VS Code: `Command Pallete` (Ctrl+Shift+P) -> `Tasks: Run Task` -> `Run tests`

### Deactivating environment
```
.venv\Scripts\deactivate.bat
```
