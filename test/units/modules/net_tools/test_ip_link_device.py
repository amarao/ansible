# Copyright (c) 2019 George Shuklin
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import pytest
from units.compat import mock
from ansible.modules.net_tools import ip_link_device


class FailJsonException(Exception):
    pass


@pytest.fixture(scope='function')
def mock_module():
    """A module with all arguments set to None and mocked fail function."""
    mock_module = mock.MagicMock()
    mock_module.params = {}
    for knob in ip_link_device.LinkDevice.knob_cmds.keys():
        mock_module.params[knob] = None
    for param in ip_link_device.LinkDevice.params_list:
        mock_module.params[param] = None
    mock_module.check_mode = False
    mock_module.run_command.return_value = (0, '', '')
    mock_module.fail_json.side_effect = FailJsonException(
        'fail_json was called'
    )
    return mock_module


@pytest.mark.parametrize('input, command', [
    # minimal testcase
    (
        {
            'type': 'veth'
        },
        'ip link add name veth1 type veth'
    ),
    # namespaces testcase
    (
        {
            'type': 'veth',
            'namespace': 'foo'
        },
        'ip netns exec foo ip link add name veth1 type veth'
    ),
    # veth options only
    (
        {
            'type': 'veth',
            'veth_options': {
                'peer_name': 'veth2'
            }
        },
        'ip link add name veth1 type veth peer name veth2'
    ),
    # veth options inside type_options
    (
        {
            'type': 'veth',
            'type_options': {
                'peer_name': 'veth2'
            }
        },
        'ip link add name veth1 type veth peer name veth2'
    ),
    # full stack of common options for the interface
    (
        {
            'type': 'veth',
            'link': 'eth0',
            'index': 1,
            'txqueuelen': 2,
            'address': '01:02:03:04:05:06',
            'broadcast': 'f1:f2:f3:f4:f5:f6',
            'mtu': 3,
            'numtxqueues': 4,
            'numrxqueues': 5,
            'gso_max_size': 6,
            'gso_max_segs': 7,
        },
        'ip link add link eth0 name veth1 txqueuelen 2 address 01:02:03:04:05:06 broadcast f1:f2:f3:f4:f5:f6 mtu 3 index 1 numtxqueues 4 numrxqueues 5 gso_max_size 6 gso_max_segs 7 type veth'  # noqa
    ),
])
def test_present_creates_veth1(mock_module, input, command):
    mock_module.params.update(input)
    mock_module.params['state'] = 'present'
    mock_module.params['name'] = 'veth1'
    mock_module.run_command.side_effect = (
        (1, '', 'Device "veth1" does not exist.\n'),
        (0, '', '')
    )
    dev = ip_link_device.LinkDevice(mock_module)
    dev.run()
    assert mock_module.run_command.call_count == 2
    assert mock_module.run_command.call_args_list[1] == mock.call(command.split())
