# localhost-throttle
Tool to throttle or redirect your localhost connections

Currently only supports redirection of **TCP** traffic.

## Usage
```
python -m localhost-throttle --in-port <in-port> --out-port <out-port> --protocols tcp
```

## Example:
```
python -m localhost-throttle --in-port 8000 --out-port 8001 --protocols tcp
```

## Current features
- Redirection of TCP traffic from one port to another
- Pretty hard to kill on Windows (unintended)