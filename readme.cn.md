[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Pandas 1.2+](https://img.shields.io/badge/pandas-1.2+-green.svg)](https://pandas.pydata.org/)

# nornir_table_inventory

nornir_table_inventory 是 [Nornir](https://github.com/nornir-automation/nornir) 的一个插件，通过表格（CSV、Excel）文件来管理 nornir 的设备清单。它甚至提供了一种隐藏的方法，可以让你的数据库或者自动化系统作为 nornir 的 inventory 数据源。

由于是表格承载，所以只支持扁平化的数据，对于 groups 和 defaults 目前不支持，后续也暂时不考虑。

## 支持的 Inventory 类

nornir_table_inventory 提供 3 种 inventory 类：
- `CSVInventory` - 通过 CSV 文件进行设备清单管理
- `ExcelInventory` - 通过 Excel（xlsx）文件进行设备清单管理
- `FlatDataInventory` - 使用 Python 的列表对象（成员是字典）进行设备清单管理，支持与数据库和自动化系统集成

## 安装

建议通过 pip 安装：

```bash
pip install nornir-table-inventory
```

## 使用示例

### 用 nornir 的配置文件加载

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

### 使用字典加载配置

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
        "sheet_name": 0,  # 可选，默认为 0（第一个工作表）
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

## 各 Inventory 类的参数

### CSVInventory 参数

```
参数：
    csv_file: CSV 文件路径，可选，默认值：inventory.csv
```

### ExcelInventory 参数

```
参数：
    excel_file: Excel 文件路径，可选，默认值：inventory.xlsx（支持 Microsoft Office Excel 2007+）
    sheet_name: 工作表索引或名称，可选，默认值：0（第一个工作表）
```

## 表格结构

| name | hostname | platform | port | username | password | city | model | netmiko_timeout | netmiko_secret |
|------|----------|----------|------|----------|----------|------|-------|----------------|----------------|
| netdevops01 | 192.168.137.201 | cisco_ios | 22 | netdevops | admin123! | bj | catalyst3750 | 60 | admin1234! |
| netdevops02 | 192.168.137.202 | cisco_ios | 22 | netdevops | admin123! | shanghai | catalyst3750 | 60 | admin1234! |

### 字段说明

- **name**：主机名称（如果提供了 hostname，则可选）
- **hostname**：设备 IP 地址或 FQDN
- **platform**：Netmiko 中的 device_type
- **port**：SSH 端口，默认值：22
- **username**、**password**：设备的用户名和密码
- **netmiko_***：以 netmiko_ 为前缀的参数，会自动传递给 Netmiko 的 ConnectHandler
- **timeout**、**conn_timeout**、**auth_timeout**、**banner_timeout**、**blocking_timeout**、**session_timeout**：会被转换为整数
- **fast_cli**：会被转换为布尔值（值为 'false'、'0' 或 'none' 时为 false，其他值为 true）
- **其他字段**：任何其他字段都会存储在主机的 data 字典中

### 名称回退行为

如果缺少 **name** 字段，插件会自动使用 **hostname** 作为主机名称。

## 示例输出

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

## 高级用法：以任意数据源作为设备清单

CSVInventory 和 ExcelInventory 类都基于 FlatDataInventory 插件。该插件允许从 Python 字典列表加载清单，实现与任意数据源的集成。

```python
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command

def get_nornir_by_your_func(some_args=None, num_workers=100):
    ''' 用你能想到的手段结合封装的 some_args 从 API 或者数据库中获取数据，进行转换，转换后数据示例如下 '''
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

## 兼容性

- **Python**：3.7+（支持 up 到 Python 3.12+）
- **Pandas**：1.2+（支持 up 到 Pandas 3.0+）
- **Nornir**：3.0+（支持 up 到 Nornir 3.5+）