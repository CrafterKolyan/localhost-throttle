# localhost-throttle
Tool to throttle or redirect your localhost connections

## Usage
```
localhost-throttle --in-port <in-port> --out-port <out-port> --protocols tcp
```

You should think about `localhost-throttle` as a wrapper around your server.<br>
`in-port` means the port on which the server listens.<br>
`out-port` means the port on which `localhost-throttle` will listen and to which client should subscribe.

## Example:
```
localhost-throttle --in-port 8000 --out-port 8001 --protocols tcp
```

## Current features
- Redirection of TCP/UDP traffic from one port to another

## Installing package
```
pip install .
```

### Requirements
- Python 3.7+
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