# vmdo - Execute actions in guest over VM channel (host component) 
#### Version 0.1 / "Fresh Tabbouli"

## Introduction
This little script allows you to execute actions inside a virtual machine that have been requested from the host/hypervisor.  
These actions are really just standard executables dropped into a directory, that will be spawned as a process.  

By joining forces with it's VM guest companion app ["vmobey"](https://github.com/doctor-love/vmobey), many great tasks can be achieved - such instructing the guest to perform system updates, reconfigure network settings and similar.  

It is like a bad/less complex version of Peter Odding's ["negotiator"](https://github.com/xolox/python-negotiator).  


## Usage
```
# cp -p vmdo.py /usr/bin/vmdo
# vmdo -t 'gw-1' -a 'start_vpn' -p 'acme_ab'
INFO: Waiting for response from VM "gw-1"
INFO: gw-1 - RC: 0 - "VPN connection "acme_ab" was successfully started"

# vmdo -t 'all' -a 'check_updates'
INFO: Waiting for response from VM "gw-1"
INFO: Waiting for response from VM "dev-1"
INFO: gw-1 - RC: 0 - "No unapplied updates are available"
INFO: dev-1 - RC: 1 - "4 unapplied security updates are available"

```

## Dependencies
- Linux (should probably work fine for Windows and GNU HURD as well, but I haven't tested it)
- Libvirt and a configured VirtIO channel called "org.rsw.vmdo.0"
- Python 3.3 or later with the standard library
