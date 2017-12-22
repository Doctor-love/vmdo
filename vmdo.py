#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

'''vmdo - Execute actions in guest over VM channel (host component)'''

DESCRIPTION = __doc__
VERSION = '0.2 / "Marvelous Maamoul"'
URL = 'https://github.com/doctor-love/vmdo'

from multiprocessing.pool import ThreadPool
from collections import namedtuple
import logging as _log
import argparse
import socket
import glob
import sys
import os

CHANNELS_DIR = '/var/lib/libvirt/qemu/channel/target/'
Channel = namedtuple('Channel', 'vm_name path')

# -----------------------------------------------------------------------------
def get_vm_name(channel_dir, channel_path):
    _log.debug('Extracting VM name from channel path "%s"' % channel_path)

    vm_name = channel_path[
        len(channel_dir) + len('domain-'):-len('/org.rsw.vmdo.0')]

    _log.debug('Extracted name from channel path: "%s"' % vm_name)
    return vm_name
    

# -----------------------------------------------------------------------------
def get_active_channels(channel_dir):
    _log.debug('Checking for active channels in "%s"' % channel_dir)

    channel_paths = glob.glob(channel_dir + 'domain-*/org.rsw.vmdo.0')

    if not channel_paths:
        raise Exception('Could not find any active VM channels for vmdo')

    channels = []

    for channel_path in channel_paths:
        channels.append(
            Channel(
                vm_name=get_vm_name(channel_dir, channel_path),
                path=channel_path))

    return channels


# -----------------------------------------------------------------------------
def get_channel_path(channel_dir, target):
    _log.debug('Checking channel path for target "%s"' % target)

    channel_glob = channel_dir + 'domain*%s' % target + '/org.rsw.vmdo.0'
    _log.debug('Channel glob for target "%s": "%s"' % (target, channel_glob))

    # Using glob here, since the naming is different between libvirt versions
    channel_path = glob.glob(channel_glob)

    if not len(channel_path) is 1:
        raise Exception('Could not find active channel for VM "%s"' % target)

    channel_path = channel_path[0]

    return channel_path


# -----------------------------------------------------------------------------
def execute_action(channel, action, timeout, params):

    channel, action, timeout, params 

    _log.debug(
        'Executing action "%s" with parameters "%s" in channel "%s"'
        % (action, params, channel.path))

    if not params:
        params = ''

    try:
        con = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        con.connect(channel.path)

    except Exception as error_msg:
        raise Exception(
            'Failed to open channel "%s": "%s"' % (channel.path, error_msg))

    try:
        payload = '%i %s %s\n' % (timeout, action, params)
        con.send(payload.encode('utf-8'))

        _log.info('Waiting for response from VM "%s"' % channel.vm_name)

        resp = con.recv(600)

        _log.debug(
            'Recieved data from channel "%s": "%s"'
            % (channel.path, str(resp)))

        status, msg = resp.decode('utf-8').split(' ', 1)
        status = int(status)

    except Exception as error_msg:
        raise Exception(
            'Error in communication over VM channel "%s": "%s"'
            % (channel.path, error_msg))

    # -------------------------------------------------------------------------
    # If action status is OK use green text, otherwise use yellow
    if status is 0:
        color = '\033[92m'
    else:
        color = '\033[93m'


    _log.info(
        '%s%s - RC: %i - "%s"%s'
        % (color, channel.vm_name, status, msg, '\033[0m'))

    return status


# -----------------------------------------------------------------------------
args = argparse.ArgumentParser(description=DESCRIPTION, epilog='URL: ' + URL)

args.add_argument(
    '-t', '--target', dest='targets', type=str, action='append',
    metavar='VM_NAME', required=True,
    help='Name of target VM/domain or "all". Can be used multiple times')

args.add_argument(
    '-a', '--action', type=str, required=True,
    metavar='ACTION_NAME', help='Name of action to perform by the target')

args.add_argument(
    '-p', '--params', type=str, metavar='"--arg-1 \'val-1\'..."',
    help='Additional parameters/arguments for the action executable')

args.add_argument(
    '-T', '--timeout', type=int, default=90, metavar='SECONDS',
    help='Timeout for actions, specified in seconds (default: %(default)s')

args.add_argument(
    '-c', '--channels-dir', type=str,
    default=CHANNELS_DIR, metavar='/path/to/channels',
    help='Path to libvirt channels directory (default: %(default)s')

args.add_argument('-v', '--verbose', action='store_true', default=False,
    help='Enable verbose debug logging')

args.add_argument('-V', '--version', action='version', version=VERSION,
    help='Display application version')


args = args.parse_args()

if args.verbose:
    log_level = _log.DEBUG

else:
    log_level = level=_log.INFO

_log.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

# -----------------------------------------------------------------------------
try:
    if 'all' in args.targets:
        _log.debug('Executing action "%s" in all running VMs' % args.action)
    
        channels = get_active_channels(args.channels_dir)
        
    else:
        _log.debug(
            'Executing action "%s" in target VM(s) "%s"'
            % (args.action, ', '.join(args.targets)))
    
        channels = []
           
        for target in args.targets:
            channels.append(
                Channel(
                    vm_name=target,
                    path=get_channel_path(args.channels_dir, target)))
    
except Exception as error_msg:
    _log.error(error_msg)
    sys.exit(3)

# -----------------------------------------------------------------------------
pool = ThreadPool(processes=(len(channels)))
results = []
status_codes = []

try:
    for channel in channels:
        results.append(
            pool.apply_async(
                execute_action,
                (channel, args.action, args.timeout, args.params)))

    for result in results:
        status_codes.append(result.get())        

except KeyboardInterrupt:
    _log.info('Interrupted by keyboard - exiting!\n')
    sys.exit(3)

except Exception as error_msg:
    _log.error('Failed to execute action: "%s"' % error_msg)
    sys.exit(1)

sys.exit(max(status_codes)) 
