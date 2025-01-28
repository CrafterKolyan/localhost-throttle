[![Tests](https://github.com/CrafterKolyan/localhost-throttle/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/CrafterKolyan/localhost-throttle/actions/workflows/tests.yml)

# localhost-throttle
Tool to throttle or redirect your localhost connections

## Usage
```
localhost-throttle --in-port <in-port> --out-port <out-port> --protocols tcp,udp --bandwidth <bandwidth>
```

You should think about `localhost-throttle` as a wrapper around your server.<br>
`in-port` means the port on which the server listens.<br>
`out-port` means the port on which `localhost-throttle` will listen and to which client should subscribe.

## Example:
```
localhost-throttle --in-port 8000 --out-port 8001 --protocols tcp --bandwidth 100000
```

## Current features
- Redirection of TCP/UDP traffic from one port to another
- Basic TCP/UDP traffic bandwidth limitting (very dumb) (will be improved in the future)

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
