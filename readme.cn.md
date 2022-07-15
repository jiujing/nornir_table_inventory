[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)


# nornir_table_inventory

nornir_table_inventory 是 [Nornir](https://github.com/nornir-automation/nornir)的一个插件，通过表格（csv、Excel）文件来管理nornir的设备清单。它甚至提供了一种隐藏的方法，可以让你的数据库或者自动化系统作为nornir的inventory数据源。

由于是表格承载，所以只支持扁平化的数据，对于groups和defaults目前不支持，后续也暂时不考虑。

nornir_table_inventory 提供2种 inventory 类 .
- `CSVInventory` 支持通过csv文件进行设备清单管理
- `ExcelInventory` 支持通过Excel（xlsx）文件进行设备清单管理
- `FlatDataInventory` 使用python的列表对象（成员是字典）进行设备清单管理

## 安装

建议通过pip安装

```bash
pip install nornir-table-inventory
```

## 使用示例

### 用nornir的配置文件加载

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



### CSVInventory arguments

```
Arguments:
    csv_file: csv文件的路径，选填，默认是inventory.csv
```

### ExcelInventory arguments

```
Arguments:
    excel_file: Excel表格文件的路径，目前支持xlsx（Microsoft Office EXCEL 2007/2010/2013/2016/2019文档的扩展名）,选填，默认值是inventory.xlsx
```

# 表格文件说明

|name|hostname|platform|port|username|password|city|model|netmiko_timeout|netmiko_secret|
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
|netdevops01|192.168.137.201|cisco_ios|22|netdevops|admin123!|bj|catalyst3750|60|admin1234!|
|netdevops02|192.168.137.202|cisco_ios|22|netdevops|admin123!|shanghai|catalyst3750|60|admin1234!|

- name：host的name

- hostname： 设备IP或者fqdn

- platform：netmiko中的device_type一一对应

- port：netmiko中的port参数

- username，password： 设备的用户名密码，暂不支持ssh key file的方式

- `netmiko_`为前缀的参数，会自动加载到ConnectHandler（Netmiko）函数中，用于构建netmiko的ssh connection的对象

- netmiko中的以下参数会自动转为int类型，`timeout conn_timeout auth_timeout banner_timeout blocking_timeout session_timeout`，如果有此字段，务必填写数字，否则做类型转换时会报错。

- netmiko中的以下参数会自动转换为布尔值，`fast_cli`。表格中赋值为`false 0 None`（不区分大小写）的值会被转为False，其余的会被转为True。

- 其余所有值都会被赋值给host的data数据中。

  上述表格加载的host对象如下，参考如下代码打印结果

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

  结果：

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
  host netmiko details: {'extras': {'timeout': 60, 'secret': 'admin1234!'}, 'hostname': None, 'port': None, 'username': None, 'password': None, 'platform':
  
  ```
  
  # 强有力的隐藏方法——以任意数据源作为设备清单

  上述的方法都是基于表格数据进行资产清单的加载，实际上述2个设备清单插件使用了一个共同的资产插件FlatDataInventory。
  它允许我们通过函数对接到我们的系统，将数据获取后，加工成为字典的列表，进而加载到nornir当中去。
  通过这个函数，我们可以使用任意数据源来记载nornir，可以是数据库、可以是我们自动化系统的api等等。
  有了它，也许你就不需要其他的sql或者csv的nornir插件了。
  ```python
  from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command


def get_nornir_by_your_func(some_args=None, num_workers=100):
    
    ''' 用你能想到的手段结合封装的some_args从api或者数据库中获取数据，进行转换，转后数据示例如下'''
    data = [{'name': 'netdevops01', 'hostname': '192.168.137.201',
             'platform': 'cisco_ios', 'port': 22, 'username': 'netdevops',
             'password': 'admin123!', 'city': 'bj', 'model': 'catalyst3750',
             'netmiko_timeout': 180, 'netmiko_secret': 'admin1234!',
             'netmiko_banner_timeout': '30', 'netmiko_conn_timeout': '20'},
            {'name': 'netdevops02', 'hostname': '192.168.137.202', 'platform':
                'cisco_ios', 'port': 22, 'username': 'netdevops', 'password': 'admin123!',
             'city': 'bj', 'model': 'catalyst3750', 'netmiko_timeout': 120,
             'netmiko_secret': 'admin1234!', 'netmiko_banner_timeout': 30,
             'netmiko_conn_timeout': 20}
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