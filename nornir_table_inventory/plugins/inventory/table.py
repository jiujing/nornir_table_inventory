import csv
import logging
from typing import Any, Dict

import pandas as pd
from nornir.core.inventory import (
    Inventory,
    Groups,
    Host,
    Hosts,
    Defaults,
    ConnectionOptions,
)

logger = logging.getLogger(__name__)


def _get_connection_options(data: Dict[str, Any]) -> Dict[str, ConnectionOptions]:
    cp = {}
    for cn, c in data.items():
        cp[cn] = ConnectionOptions(
            hostname=c.get("hostname"),
            port=c.get("port"),
            username=c.get("username"),
            password=c.get("password"),
            platform=c.get("platform"),
            extras=c.get("extras"),
        )
    return cp


def _get_host_data(data: Dict[str, Any]) -> Dict[str, Any]:
    no_data_fields = ['name', 'hostname', 'port', 'username', 'password', 'platform']
    resp_data = {}
    netmiko_prefix = 'netmiko_'
    for k, v in data.items():
        if (k not in no_data_fields) and (netmiko_prefix not in k):
            resp_data[k] = v
    return resp_data


def _get_host_netmiko_options(data: Dict[str, Any]) -> Dict[str, Any]:
    extra_opts = {}
    netmiko_options = {
        'netmiko': {
            'extras': {
            }
        }
    }
    """:cvar
    conn_timeout=5,
        auth_timeout=None,  # Timeout to wait for authentication response
        banner_timeout=15,  # Timeout to wait for the banner to be presented (post TCP-connect)
        # Other timeouts
        blocking_timeout=20,  # Read blocking timeout
        timeout=100,  # TCP connect timeout | overloaded to read-loop timeout
        session_timeout=60,  # Used for locking/sharing the connection
    
    
    """
    int_keys = 'timeout conn_timeout auth_timeout banner_timeout blocking_timeout session_timeout'.split()
    bool_keys = 'fast_cli'.split()
    netmiko_prefix = 'netmiko_'
    for k, v in data.items():
        if netmiko_prefix in k:
            new_k = k.replace(netmiko_prefix, '')

            if new_k in int_keys:
                extra_opts[new_k] = int(v)
            elif new_k in bool_keys:
                if str(v).lower() in ['0', 'false', 'none']:
                    extra_opts[new_k] = False
                else:
                    extra_opts[new_k] = True
            else:
                extra_opts[new_k] = v

    if extra_opts:
        netmiko_options['netmiko']['extras'] = extra_opts
        return _get_connection_options(netmiko_options)
    else:
        return {}


def _get_host_obj(data: Dict[str, Any]) -> Host:
    return Host(
        name=data.get('name'),
        hostname=data.get("hostname"),
        port=data.get("port", 22),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=_get_host_data(data),
        groups=None,
        defaults={},
        connection_options=_get_host_netmiko_options(data),
    )


class CSVInventory:
    def __init__(
            self,
            csv_file: str = "inventory.csv"
    ) -> None:
        self.hosts_list = []
        with open(csv_file, mode='r', encoding='utf8') as f:
            for i in csv.DictReader(f):
                self.hosts_list.append(i)

    def load(self) -> Inventory:
        defaults = Defaults()
        groups = Groups()
        hosts = Hosts()

        for host_dict in self.hosts_list:
            hosts[host_dict['name']] = _get_host_obj(host_dict)

        return Inventory(hosts=hosts, groups=groups, defaults=defaults)


class ExcelInventory(CSVInventory):
    def __init__(
            self,
            excel_file: str = "inventory.xlsx"
    ) -> None:
        self.hosts_list = []
        dataframe = pd.read_excel(excel_file)
        items = dataframe.to_dict(orient='records')
        self.hosts_list = items


if __name__ == '__main__':
    t = ExcelInventory()
    inv = t.load()
    print(inv)
