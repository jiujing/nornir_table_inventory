[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Pandas 1.2+](https://img.shields.io/badge/pandas-1.2+-green.svg)](https://pandas.pydata.org/)

# nornir_table_inventory

The nornir_table_inventory is a [Nornir](https://github.com/nornir-automation/nornir) plugin for inventory management. It allows you to manage inventory through table files (CSV or Excel) and provides a flexible way to use your database or automation system as an inventory source.

Currently, it only supports Netmiko connections. It doesn't support groups or defaults since it focuses on flat data stored in two-dimensional table files.

## Inventory Classes

nornir_table_inventory supports 3 inventory classes:
- `CSVInventory` - Manages inventory through CSV files
- `ExcelInventory` - Manages inventory through Excel (xlsx) files
- `FlatDataInventory` - Manages inventory through Python list of dictionaries, allowing integration with databases and automation systems

## Installing

```bash
pip install nornir-table-inventory
```

## Example Usage

### Using Nornir Configuration File

```yaml
---
inventory:
      plugin: CSVInventory
      options:
          csv_file: "inventory.csv"

runner:
    plugin: threaded
    options:
        num_workers: 100
```

```python
from nornir import InitNornir

nr = InitNornir(config_file=r'config.yml')

for n, h in nr.inventory.hosts.items():
    print('host name:', n)
    print('host hostname:', h.hostname)
    print('host username:', h.username)
    print('host password:', h.password)
    print('host platform:', h.platform)
    print('host port:', h.port)
    print('host data:', h.data)
    print('host netmiko details:', h.connection_options.get('netmiko').dict())
    print('='*150)
```

### Using InitNornir with Dict Configuration

```python
from nornir import InitNornir

runner = {
    "plugin": "threaded",
    "options": {
        "num_workers": 100,
    },
}
inventory = {
    "plugin": "ExcelInventory",
    "options": {
        "excel_file": "inventory.xlsx",
        "sheet_name": 0,  # Optional, default is 0 (first sheet)
    },
}

nr = InitNornir(runner=runner, inventory=inventory)

for n, h in nr.inventory.hosts.items():
    print('host name:', n)
    print('host hostname:', h.hostname)
    print('host username:', h.username)
    print('host password:', h.password)
    print('host platform:', h.platform)
    print('host port:', h.port)
    print('host data:', h.data)
    print('host netmiko details:', h.connection_options.get('netmiko').dict())
    print('='*150)
```

## Inventory Class Arguments

### CSVInventory Arguments

```
Arguments:
    csv_file: CSV file path, optional, default: inventory.csv
```

### ExcelInventory Arguments

```
Arguments:
    excel_file: Excel file path, optional, default: inventory.xlsx (supports Microsoft Office Excel 2007+)
    sheet_name: Sheet index or name, optional, default: 0 (first sheet)
```

## Table Structure

| name | hostname | platform | port | username | password | city | model | netmiko_timeout | netmiko_secret |
|------|----------|----------|------|----------|----------|------|-------|----------------|----------------|
| netdevops01 | 192.168.137.201 | cisco_ios | 22 | netdevops | admin123! | bj | catalyst3750 | 60 | admin1234! |
| netdevops02 | 192.168.137.202 | cisco_ios | 22 | netdevops | admin123! | shanghai | catalyst3750 | 60 | admin1234! |

### Field Descriptions

- **name**: Host name (optional if hostname is provided)
- **hostname**: IP address or FQDN of the host
- **platform**: Netmiko device_type
- **port**: SSH port, default: 22
- **username**, **password**: Host credentials
- **netmiko_***: Prefix for Netmiko-specific parameters, which will be passed to Netmiko's ConnectHandler
- **timeout**, **conn_timeout**, **auth_timeout**, **banner_timeout**, **blocking_timeout**, **session_timeout**: Will be converted to integers
- **fast_cli**: Will be converted to boolean (values of 'false', '0', or 'none' are false, others are true)
- **Other fields**: Any other fields will be stored in the host's data dictionary

### Name Fallback Behavior

If the **name** field is missing, the plugin will automatically use the **hostname** as the host name.

## Example Output

```shell
host name: netdevops01
host hostname: 192.168.137.201
host username: netdevops
host password: admin123!
host platform: cisco_ios
host port: 22
host data: {'city': 'bj', 'model': 'catalyst3750'}
host netmiko details: {'extras': {'timeout': 60, 'secret': 'admin1234!'}, 'hostname': None, 'port': None, 'username': None, 'password': None, 'platform': None}
======================================================================================================================================================
host name: netdevops02
host hostname: 192.168.137.202
host username: netdevops
host password: admin123!
host platform: cisco_ios
host port: 22
host data: {'city': 'shanghai', 'model': 'catalyst3750'}
host netmiko details: {'extras': {'timeout': 60, 'secret': 'admin1234!'}, 'hostname': None, 'port': None, 'username': None, 'password': None, 'platform': None}
```

## Advanced Usage: Any Data Source as Inventory

The CSVInventory and ExcelInventory classes are both based on the FlatDataInventory plugin. This plugin allows loading inventory from a Python list of dictionaries, enabling integration with any data source.

```python
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command

def get_nornir_by_your_func(some_args=None, num_workers=100):
    """Use any method to get data (e.g., SQL or REST API) and transform it into the required format"""
    data = [
        {
            'name': 'netdevops01', 
            'hostname': '192.168.137.201',
            'platform': 'cisco_ios', 
            'port': 22, 
            'username': 'netdevops',
            'password': 'admin123!', 
            'city': 'bj', 
            'model': 'catalyst3750',
            'netmiko_timeout': 180, 
            'netmiko_secret': 'admin1234!',
            'netmiko_banner_timeout': '30', 
            'netmiko_conn_timeout': '20'
        },
        {
            'name': 'netdevops02', 
            'hostname': '192.168.137.202', 
            'platform': 'cisco_ios', 
            'port': 22, 
            'username': 'netdevops', 
            'password': 'admin123!',
            'city': 'bj', 
            'model': 'catalyst3750', 
            'netmiko_timeout': 120,
            'netmiko_secret': 'admin1234!', 
            'netmiko_banner_timeout': 30,
            'netmiko_conn_timeout': 20
        }
    ]
    
    runner = {
        "plugin": "threaded",
        "options": {
            "num_workers": num_workers,
        },
    }
    
    inventory = {
        "plugin": "FlatDataInventory",
        "options": {
            "data": data,
        },
    }
    
    nr = InitNornir(runner=runner, inventory=inventory)
    return nr

if __name__ == '__main__':
    nr = get_nornir_by_your_func()
    bj_devs = nr.filter(city='bj')
    r = bj_devs.run(task=netmiko_send_command, command_string='display version')
    print_result(r)
```

## Compatibility

- **Python**: 3.7+ (supports up to Python 3.12+)
- **Pandas**: 1.2+ (supports up to Pandas 3.0+)
- **Nornir**: 3.0+ (supports up to Nornir 3.5+)