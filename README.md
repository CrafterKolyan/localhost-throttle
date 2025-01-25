# localhost-throttle
Tool to throttle or redirect your localhost connections

## Usage
```
python -m localhost_throttle --in-port <in-port> --out-port <out-port> --protocols tcp
```

You should think about `localhost-throttle` as a wrapper around your server.<br>
`in-port` means the port on which the server listens.<br>
`out-port` means the port on which `localhost-throttle` will listen and to which client should subscribe.

## Example:
```
python -m localhost_throttle --in-port 8000 --out-port 8001 --protocols tcp
```

## Current features
- Redirection of TCP/UDP traffic from one port to another

## Known bugs
- UDP client will receive traffic from a newly generated socket rather from `out-port`