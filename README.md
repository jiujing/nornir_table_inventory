# ns_nornir_table_inventory

[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A powerful Nornir inventory plugin that enables network automation engineers to manage device inventories using table-based formats (CSV or Excel files) instead of traditional YAML/JSON configurations. Perfect for teams transitioning to automation or integrating with existing databases and CMDB systems.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Inventory Classes](#inventory-classes)
- [Usage Examples](#usage-examples)
- [Table Format Specification](#table-format-specification)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

The `ns_nornir_table_inventory` is a plugin for [Nornir](https://github.com/nornir-automation/nornir) 3.x that allows you to manage your network device inventory using familiar spreadsheet formats. Instead of maintaining complex YAML or JSON files, you can use CSV files or Excel spreadsheets that your team already understands.

### Why Use This Plugin?

- **Familiar Interface**: Use CSV or Excel files that non-programmers can easily edit
- **Database Integration**: Connect to any database or API using the `FlatDataInventory` class
- **Simple Migration**: Easy transition from spreadsheet-based inventory to automation
- **Flat Data Structure**: Focuses on practical, two-dimensional data structures
- **Netmiko Ready**: Built-in support for Netmiko connection parameters

### Limitations

- **Netmiko Only**: This plugin currently supports Netmiko connections only
- **No Groups/Defaults**: Focuses on flat data structures; doesn't support Nornir groups or defaults
- **Flat Data Model**: Not suitable for complex hierarchical inventory structures

## Key Features

1. **Three Inventory Classes**:
   - `CSVInventory` - Load inventory from CSV files
   - `ExcelInventory` - Load inventory from Excel (.xlsx) files
   - `FlatDataInventory` - Load inventory from Python lists (for database/API integration)

2. **Flexible Field Handling**:
   - Standard fields: name, hostname, platform, port, username, password
   - Netmiko-specific fields with `netmiko_` prefix
   - Custom data fields for any additional information

3. **Automatic Type Conversion**:
   - Integer conversion for timeout fields
   - Boolean conversion for flags like `fast_cli`
   - NaN/None handling for missing values

## Installation

Install via pip:

```bash
pip install ns-nornir-table-inventory
```

Install from source:

```bash
git clone https://github.com/nstamoul/ns_nornir_table_inventory.git
cd ns_nornir_table_inventory
pip install .
```

### Requirements

- Python >= 3.7
- nornir >= 3.0.0
- pandas >= 1.2.0

## Quick Start

### 1. Create an Inventory File

Create `inventory.csv`:

```csv
name,hostname,platform,port,username,password,city,netmiko_timeout,netmiko_secret
netdevops01,192.168.137.201,cisco_ios,22,netdevops,admin123!,beijing,60,admin1234!
netdevops02,192.168.137.202,cisco_ios,22,netdevops,admin123!,shanghai,60,admin1234!
```

### 2. Create a Nornir Configuration

Create `config.yml`:

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

### 3. Use in Your Script

```python
from nornir import InitNornir
from nornir_netmiko import netmiko_send_command

# Initialize Nornir with the CSV inventory
nr = InitNornir(config_file='config.yml')

# Run a command on all devices
result = nr.run(task=netmiko_send_command, command_string='show version')

# Access host information
for name, host in nr.inventory.hosts.items():
    print(f"Host: {name}")
    print(f"  IP: {host.hostname}")
    print(f"  Platform: {host.platform}")
    print(f"  Custom Data: {host.data}")
```

## Inventory Classes

### CSVInventory

Loads inventory from CSV files.

```python
from nornir import InitNornir

inventory = {
    "plugin": "CSVInventory",
    "options": {
        "csv_file": "inventory.csv"  # Optional, defaults to "inventory.csv"
    }
}

nr = InitNornir(inventory=inventory)
```

**Arguments:**
- `csv_file` (str, optional): Path to CSV file. Default: `"inventory.csv"`

### ExcelInventory

Loads inventory from Excel (.xlsx) files.

```python
from nornir import InitNornir

inventory = {
    "plugin": "ExcelInventory",
    "options": {
        "excel_file": "inventory.xlsx",
        "excel_sheet": "Sheet1"
    }
}

nr = InitNornir(inventory=inventory)
```

**Arguments:**
- `excel_file` (str): Path to Excel file (.xlsx format, Microsoft Office Excel 2007+)
- `excel_sheet` (str): Name of the sheet to read from

**Special Behavior:**
- Automatically maps `device_type` → `platform`
- Automatically maps `ip` → `hostname`
- Removes legacy fields: `secret`, `verbose`, `host`, `global_delay_factor`
- Uses `ip` as fallback if `name` is empty

### FlatDataInventory

Loads inventory from Python list of dictionaries. Perfect for database or API integration.

```python
from nornir import InitNornir

# Fetch data from your database, API, or any source
data = [
    {
        'name': 'router1',
        'hostname': '192.168.1.1',
        'platform': 'cisco_ios',
        'port': 22,
        'username': 'admin',
        'password': 'secret',
        'netmiko_timeout': 60
    }
]

inventory = {
    "plugin": "FlatDataInventory",
    "options": {
        "data": data
    }
}

nr = InitNornir(inventory=inventory)
```

**Arguments:**
- `data` (List[Dict]): List of dictionaries, each representing a host

## Usage Examples

### Example 1: Using CSV with Configuration File

**config.yml:**
```yaml
inventory:
  plugin: CSVInventory
  options:
    csv_file: "inventory.csv"

runner:
  plugin: threaded
  options:
    num_workers: 100
```

**Python script:**
```python
from nornir import InitNornir

nr = InitNornir(config_file='config.yml')

for name, host in nr.inventory.hosts.items():
    print(f'Host: {name}')
    print(f'  IP: {host.hostname}')
    print(f'  Platform: {host.platform}')
    print(f'  Custom Data: {host.data}')
    print(f'  Netmiko Options: {host.connection_options.get("netmiko").dict()}')
    print('=' * 80)
```

### Example 2: Using Excel Programmatically

```python
from nornir import InitNornir

inventory = {
    "plugin": "ExcelInventory",
    "options": {
        "excel_file": "network_devices.xlsx",
        "excel_sheet": "Production"
    }
}

runner = {
    "plugin": "threaded",
    "options": {
        "num_workers": 50
    }
}

nr = InitNornir(inventory=inventory, runner=runner)

# Filter devices by custom field
beijing_devices = nr.filter(city='beijing')
result = beijing_devices.run(task=some_task)
```

### Example 3: Database Integration with FlatDataInventory

```python
from nornir import InitNornir
from nornir_netmiko import netmiko_send_command
from nornir_utils.plugins.functions import print_result
import psycopg2  # or any other database driver

def get_nornir_from_database():
    """Fetch inventory from PostgreSQL database"""
    # Connect to database
    conn = psycopg2.connect(
        dbname="network_inventory",
        user="admin",
        password="password",
        host="localhost"
    )

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            device_name as name,
            ip_address as hostname,
            device_type as platform,
            ssh_port as port,
            username,
            password,
            site_location as city,
            timeout as netmiko_timeout,
            enable_secret as netmiko_secret
        FROM network_devices
        WHERE active = true
    """)

    # Convert to list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    # Initialize Nornir with database data
    inventory = {
        "plugin": "FlatDataInventory",
        "options": {"data": data}
    }

    runner = {
        "plugin": "threaded",
        "options": {"num_workers": 100}
    }

    return InitNornir(inventory=inventory, runner=runner)

# Use it
nr = get_nornir_from_database()
result = nr.run(task=netmiko_send_command, command_string='show version')
print_result(result)
```

### Example 4: REST API Integration

```python
import requests
from nornir import InitNornir

def get_nornir_from_api():
    """Fetch inventory from REST API"""
    # Fetch from your CMDB or API
    response = requests.get('https://api.example.com/network/devices')
    devices = response.json()

    # Transform API data to inventory format
    data = []
    for device in devices:
        data.append({
            'name': device['hostname'],
            'hostname': device['management_ip'],
            'platform': device['vendor_os'],
            'port': device.get('ssh_port', 22),
            'username': device['credentials']['username'],
            'password': device['credentials']['password'],
            'location': device['site'],
            'device_role': device['role'],
            'netmiko_timeout': device.get('timeout', 60)
        })

    inventory = {
        "plugin": "FlatDataInventory",
        "options": {"data": data}
    }

    return InitNornir(inventory=inventory)

nr = get_nornir_from_api()
```

## Table Format Specification

### Required Columns

| Column | Type | Description |
|--------|------|-------------|
| `name` | string | Unique identifier for the host |
| `hostname` | string | IP address or FQDN of the device |
| `platform` | string | Netmiko device_type (e.g., `cisco_ios`, `juniper_junos`) |
| `port` | integer | SSH port number (typically 22) |
| `username` | string | SSH username |
| `password` | string | SSH password |

### Optional Columns

#### Netmiko-Specific Fields

Prefix any Netmiko parameter with `netmiko_` to pass it to the connection handler:

| Column | Type | Description |
|--------|------|-------------|
| `netmiko_timeout` | integer | Connection timeout in seconds |
| `netmiko_secret` | string | Enable password/secret |
| `netmiko_conn_timeout` | integer | TCP connection timeout |
| `netmiko_auth_timeout` | integer | Authentication timeout |
| `netmiko_banner_timeout` | integer | Banner timeout |
| `netmiko_blocking_timeout` | integer | Read blocking timeout |
| `netmiko_session_timeout` | integer | Session timeout |
| `netmiko_fast_cli` | boolean | Enable fast CLI mode |

#### Custom Data Fields

Any column not matching the above will be stored in `host.data`:

```csv
name,hostname,platform,port,username,password,city,model,rack_location
router1,10.0.0.1,cisco_ios,22,admin,pass,NYC,ASR1000,A-1-5
```

Results in:
```python
host.data = {
    'city': 'NYC',
    'model': 'ASR1000',
    'rack_location': 'A-1-5'
}
```

### Type Conversion Rules

1. **Integer Fields**: These fields are automatically converted to integers:
   - `timeout`, `conn_timeout`, `auth_timeout`, `banner_timeout`
   - `blocking_timeout`, `session_timeout`
   - **Warning**: If you define these columns, you must provide values (not empty/None)

2. **Boolean Fields**:
   - `fast_cli` is converted to boolean
   - Values `"false"`, `"0"`, `"none"` (case-insensitive) → `False`
   - All other values → `True`

3. **Empty Values**:
   - Empty strings, `NaN`, and `None` are handled gracefully
   - Converted to `None` in the inventory

### Example Table

**inventory.csv:**
```csv
name,hostname,platform,port,username,password,city,model,netmiko_timeout,netmiko_secret,netmiko_fast_cli
netdevops01,192.168.137.201,cisco_ios,22,netdevops,admin123!,beijing,catalyst3750,60,admin1234!,true
netdevops02,192.168.137.202,cisco_ios,22,netdevops,admin123!,shanghai,catalyst3750,60,admin1234!,false
switch01,10.0.0.10,cisco_nxos,22,admin,secret,beijing,nexus9k,90,enable_secret,true
```

**Result when loaded:**
```python
# Host: netdevops01
{
    'name': 'netdevops01',
    'hostname': '192.168.137.201',
    'platform': 'cisco_ios',
    'port': 22,
    'username': 'netdevops',
    'password': 'admin123!',
    'data': {
        'city': 'beijing',
        'model': 'catalyst3750'
    },
    'connection_options': {
        'netmiko': {
            'extras': {
                'timeout': 60,
                'secret': 'admin1234!',
                'fast_cli': True
            }
        }
    }
}
```

## Advanced Usage

### Combining Multiple Data Sources

```python
from nornir import InitNornir
import pandas as pd

def get_combined_inventory():
    """Combine data from CSV, Excel, and database"""
    data = []

    # Load from CSV
    csv_data = pd.read_csv('core_routers.csv').to_dict('records')
    data.extend(csv_data)

    # Load from Excel
    excel_data = pd.read_excel('access_switches.xlsx').to_dict('records')
    data.extend(excel_data)

    # Add data from database
    # db_data = fetch_from_database()
    # data.extend(db_data)

    inventory = {
        "plugin": "FlatDataInventory",
        "options": {"data": data}
    }

    return InitNornir(inventory=inventory)
```

### Dynamic Inventory Updates

```python
def refresh_inventory(nr, new_devices):
    """Add new devices to running Nornir instance"""
    for device in new_devices:
        host_obj = _get_host_obj(device)
        nr.inventory.hosts[device['name']] = host_obj
```

### Using with Nornir Filters

```python
from nornir import InitNornir

nr = InitNornir(config_file='config.yml')

# Filter by platform
ios_devices = nr.filter(platform='cisco_ios')

# Filter by custom field
beijing_devices = nr.filter(city='beijing')

# Complex filtering
production_routers = nr.filter(
    lambda h: h.data.get('environment') == 'production'
    and 'router' in h.data.get('device_type', '').lower()
)
```

## API Reference

### Helper Functions

The following helper functions are available in `ns_nornir_table_inventory.plugins.inventory.table`:

#### `_empty(x: Any) -> bool`

Checks if a value is empty (None, NaN, or empty string).

```python
from ns_nornir_table_inventory.plugins.inventory.table import _empty

_empty(None)        # True
_empty(float('nan')) # True
_empty('')          # True
_empty('value')     # False
```

#### `_get_connection_options(data: Dict) -> Dict[str, ConnectionOptions]`

Creates Nornir ConnectionOptions objects from dictionary data.

#### `_get_host_data(data: Dict) -> Dict`

Extracts custom host data (fields that aren't standard or netmiko-prefixed).

#### `_get_host_netmiko_options(data: Dict) -> Dict`

Processes netmiko-specific fields and creates ConnectionOptions.

#### `_get_host_obj(data: Dict) -> Host`

Creates a Nornir Host object from dictionary data.

### Plugin Registration

These plugins are automatically registered with Nornir through entry points:

```python
[tool.poetry.plugins."nornir.plugins.inventory"]
"FlatDataInventory" = "ns_nornir_table_inventory.plugins.inventory.table:FlatDataInventory"
"CSVInventory" = "ns_nornir_table_inventory.plugins.inventory.table:CSVInventory"
"ExcelInventory" = "ns_nornir_table_inventory.plugins.inventory.table:ExcelInventory"
```

## Troubleshooting

### Common Issues

**1. `int() argument must be a string or a number, not 'NoneType'`**

This occurs when timeout fields are defined in headers but have empty values.

**Solution**: Ensure all timeout fields have values if the column exists:
```csv
# Bad
name,hostname,platform,port,username,password,netmiko_timeout
router1,10.0.0.1,cisco_ios,22,admin,pass,

# Good
name,hostname,platform,port,username,password,netmiko_timeout
router1,10.0.0.1,cisco_ios,22,admin,pass,60
```

**2. `HOST name must not be empty`**

This error occurs when a row has an empty `name` field.

**Solution**: Ensure all rows have a valid name, or the plugin will use the hostname as fallback (Excel only).

**3. Connection Issues**

If Netmiko connections fail, check:
- Correct `platform` value (must match Netmiko device types)
- Network connectivity to `hostname`
- Valid credentials (`username`, `password`, `netmiko_secret`)
- Appropriate timeout values

**4. Excel File Not Found**

**Solution**: Use absolute paths or ensure the file is in the working directory:
```python
import os

excel_file = os.path.abspath('inventory.xlsx')
inventory = {
    "plugin": "ExcelInventory",
    "options": {
        "excel_file": excel_file,
        "excel_sheet": "Sheet1"
    }
}
```

### Debug Mode

Enable logging to see what's happening:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

from nornir import InitNornir
nr = InitNornir(config_file='config.yml')
```

## Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

- Use the [GitHub issue tracker](https://github.com/nstamoul/ns_nornir_table_inventory/issues)
- Include Python version, Nornir version, and error messages
- Provide minimal reproduction examples

### Development Setup

```bash
# Clone the repository
git clone https://github.com/nstamoul/ns_nornir_table_inventory.git
cd ns_nornir_table_inventory

# Install with dev dependencies
pip install poetry
poetry install

# Run tests (when available)
poetry run pytest
```

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Roadmap

Potential future enhancements:

- [ ] Add comprehensive test suite
- [ ] Support for additional connection types (NAPALM, Scrapli)
- [ ] Group support for hierarchical inventories
- [ ] JSON inventory support
- [ ] Inventory validation and schema checking
- [ ] Caching for large inventories
- [ ] Async inventory loading

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Nornir](https://github.com/nornir-automation/nornir) - The network automation framework
- [Netmiko](https://github.com/ktbyers/netmiko) - Multi-vendor SSH library
- [Pandas](https://pandas.pydata.org/) - Data manipulation library

## Links

- **PyPI**: https://pypi.org/project/ns-nornir-table-inventory/
- **Repository**: https://github.com/nstamoul/ns_nornir_table_inventory
- **Documentation**: [README.md](https://github.com/nstamoul/ns_nornir_table_inventory/blob/main/README.md)
- **Issue Tracker**: https://github.com/nstamoul/ns_nornir_table_inventory/issues

## Support

If you find this project useful, please consider:
- Starring the repository on GitHub
- Reporting bugs and suggesting features
- Contributing code or documentation
- Sharing with the network automation community

---

**Author**: nstamoul <nstamoul0@gmail.com>

**Version**: 0.4.5
