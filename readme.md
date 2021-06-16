[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)


# nornir_table_inventory

The nornir_table_inventory is [Nornir](https://github.com/nornir-automation/nornir) plugin for inventory.It can manage inventory by table file(CSV or Excel).
Netmiko connections support only.

It doesn't support groups or defaults,because it focuses on flat data,and the data lies in table file of two-dimensional.



nornir_table_inventory supports 2  inventory classes .
- `CSVInventory` manages inventory by csv file
- `ExcelInventory` manages inventory by excel(xlsx) file

## Installing


```bash
pip install nornir-table-inventory
```

## Example usage

### Using the Nornir configuration file

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
for n,h in nr.inventory.hosts.items():
    print(n, h.dict())
```


### Using the InitNornir function by dict data

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
    },
}

nr = InitNornir(runner=runner, inventory=inventory)
for n,h in nr.inventory.hosts.items():
    print(n, h.dict())
```



### CSVInventory arguments

```
Arguments:
    csv_file: csv file path，optional，default:inventory.csv
```

### ExcelInventory arguments

```
Arguments:
    excel_file: excel file path，optional，default:inventory.xlsx（Microsoft Office EXCEL 2007/2010/2013/2016/2019）
```

# Table Instructions

|name|hostname|platform|port|username|password|city|model|netmiko_timeout|netmiko_secret|
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
|netdevops01|192.168.137.201|cisco_ios|22|netdevops|admin123!|bj|catalyst3750|60|admin1234!|
|netdevops02|192.168.137.202|cisco_ios|22|netdevops|admin123!|shanghai|catalyst3750|60|admin1234!|

- name：name of host

- hostname： IP or fqdn of host

- platform：netmiko's device_type

- port：port of host,netmiko's port

- username，password： username adn password of host

- `netmiko_`prefix variables，will load into ConnectHandler（Netmiko）function to build netmiko ssh connection object.

- `timeout conn_timeout auth_timeout banner_timeout blocking_timeout session_timeout` will be converted into int.If you define it in table's headers，you must assignment it，otherwise it will raise exception ，because it will call `int(None)`.

- netmiko's `fast_cli` will be converted into boolean.values of  `false 0 None`(Case insensitive)will be converted into False，others will be converted into True。

- others data such as city or model (any field name you can define) in the table will be host's data.


  Above table will be used as following codes and result

  ```python
  nr = InitNornir(runner=runner, inventory=inventory)
  for n,h in nr.inventory.hosts.items():
      print(n, h.dict())
  ```

  Results：

  ```shell
  netdevops01 {'name': 'netdevops01', 'connection_options': {'netmiko': {'extras': {'timeout': 60, 'secret': 'admin1234!'}, 'hostname': None, 'port': 
  None, 'username': None, 'password': None, 'platform': None}}, 'groups': [], 'data': {'city': 'bj', 'model': 'catalyst3750'}, 'hostname': '192.168.137.201', 'port': '22', 'username': 'netdevops', 'password': 'admin123!', 'platform': 'cisco_ios'}
  netdevops02 {'name': 'netdevops02', 'connection_options': {'netmiko': {'extras': {'timeout': 60, 'secret': 'admin1234!'}, 'hostname': None, 'port': 
  None, 'username': None, 'password': None, 'platform': None}}, 'groups': [], 'data': {'city': 'shanghai', 'model': 'catalyst3750'}, 'hostname': '192.168.137.202', 'port': '22', 'username': 'netdevops', 'password': 'admin123!', 'platform': 'cisco_ios'}
  ```

  