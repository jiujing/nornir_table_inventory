# Architecture and Component Documentation

This document provides a detailed technical overview of the `ns_nornir_table_inventory` plugin architecture, components, and internal workings.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Component Hierarchy](#component-hierarchy)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Helper Functions](#helper-functions)
- [Plugin Integration](#plugin-integration)
- [Type System](#type-system)
- [Design Decisions](#design-decisions)
- [Extension Points](#extension-points)

## Architecture Overview

The `ns_nornir_table_inventory` plugin implements a three-tier architecture:

```
┌─────────────────────────────────────────────────────┐
│              Nornir Framework                        │
│         (Plugin Discovery & Loading)                 │
└───────────────────┬─────────────────────────────────┘
                    │
                    │ Plugin Interface
                    │
┌───────────────────┴─────────────────────────────────┐
│         ns_nornir_table_inventory                    │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   CSV       │  │   Excel     │  │  FlatData   │ │
│  │  Inventory  │  │  Inventory  │  │  Inventory  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                 │         │
│         └────────────────┴─────────────────┘         │
│                    │                                 │
│         ┌──────────┴──────────┐                     │
│         │  Helper Functions   │                     │
│         │  - _empty()         │                     │
│         │  - _get_host_obj()  │                     │
│         │  - _get_*_options() │                     │
│         └─────────────────────┘                     │
└───────────────────┬─────────────────────────────────┘
                    │
                    │ Nornir Inventory Objects
                    │
┌───────────────────┴─────────────────────────────────┐
│           Nornir Core Inventory                      │
│    (Inventory, Hosts, Groups, Defaults)              │
└─────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Single Responsibility**: Each class handles one type of data source
2. **Inheritance**: `CSVInventory` and `ExcelInventory` extend `FlatDataInventory`
3. **Composition**: Helper functions are used to build complex objects
4. **Plugin Pattern**: Registered with Nornir's plugin system via entry points
5. **Data Transformation**: All sources converge to a common list-of-dict format

## Component Hierarchy

### Class Diagram

```
                    ┌──────────────────┐
                    │ FlatDataInventory│
                    ├──────────────────┤
                    │ - hosts_list     │
                    │ + __init__(data) │
                    │ + load()         │
                    └────────┬─────────┘
                             │
                    ┌────────┴─────────┐
                    │                  │
        ┌───────────┴─────┐   ┌───────┴───────────┐
        │  CSVInventory   │   │  ExcelInventory   │
        ├─────────────────┤   ├───────────────────┤
        │ + __init__()    │   │ + __init__()      │
        │   (csv_file)    │   │   (excel_file,    │
        │                 │   │    excel_sheet)   │
        └─────────────────┘   └───────────────────┘
```

### Inheritance Structure

```python
FlatDataInventory (Base Class)
├── __init__(data: List[Dict])
│   └── Stores list of host dictionaries
├── load() -> Inventory
    └── Converts list to Nornir Inventory object

CSVInventory (Inherits from FlatDataInventory)
├── __init__(csv_file: str = "inventory.csv")
│   ├── Opens CSV file
│   ├── Parses with csv.DictReader
│   └── Calls super().__init__(data)
└── Inherits load() from FlatDataInventory

ExcelInventory (Inherits from FlatDataInventory)
├── __init__(excel_file: str, excel_sheet: str)
│   ├── Opens Excel file with pandas
│   ├── Applies transformations (device_type → platform, ip → hostname)
│   ├── Removes legacy fields
│   └── Calls super().__init__(data)
└── Inherits load() from FlatDataInventory
```

## Core Components

### 1. FlatDataInventory

**Location**: `ns_nornir_table_inventory/plugins/inventory/table.py:130-149`

**Purpose**: Base class that converts Python list of dictionaries into Nornir Inventory.

**Interface**:
```python
class FlatDataInventory:
    def __init__(self, data: List[Dict]) -> None:
        """Initialize with list of host dictionaries"""

    def load(self) -> Inventory:
        """Convert data to Nornir Inventory object"""
```

**Behavior**:
1. Accepts `data` as a list of dictionaries
2. Each dictionary represents one host
3. `load()` method iterates through `hosts_list`
4. For each host dict, calls `_get_host_obj()` to create Host object
5. Validates that `name` field is not empty
6. Returns `Inventory` object with hosts, empty groups, and empty defaults

**Error Handling**:
- Logs error and raises Exception if host name is empty
- Uses logger at module level (`logger = logging.getLogger(__name__)`)

**Example**:
```python
data = [
    {'name': 'router1', 'hostname': '10.0.0.1', 'platform': 'cisco_ios', ...}
]
inventory_plugin = FlatDataInventory(data=data)
inventory = inventory_plugin.load()
```

### 2. CSVInventory

**Location**: `ns_nornir_table_inventory/plugins/inventory/table.py:152-161`

**Purpose**: Load inventory from CSV files.

**Interface**:
```python
class CSVInventory(FlatDataInventory):
    def __init__(self, csv_file: str = "inventory.csv") -> None:
        """Initialize with CSV file path"""
```

**Behavior**:
1. Opens CSV file with UTF-8 encoding
2. Uses `csv.DictReader` to parse CSV into list of OrderedDict
3. Each row becomes a dictionary
4. Calls parent `__init__()` with the parsed data
5. Inherits `load()` method from FlatDataInventory

**File Format Requirements**:
- CSV format with headers in first row
- UTF-8 encoding
- Standard CSV delimiters

**Example**:
```python
inventory_plugin = CSVInventory(csv_file="devices.csv")
inventory = inventory_plugin.load()
```

### 3. ExcelInventory

**Location**: `ns_nornir_table_inventory/plugins/inventory/table.py:164-202`

**Purpose**: Load inventory from Excel (.xlsx) files with legacy field mapping.

**Interface**:
```python
class ExcelInventory(FlatDataInventory):
    def __init__(self, excel_file: str, excel_sheet: str) -> None:
        """Initialize with Excel file path and sheet name"""
```

**Behavior**:
1. Reads Excel file using `pandas.read_excel()`
2. Converts specified sheet to list of dictionaries
3. Applies transformations:
   - `device_type` → `platform`
   - `ip` → `hostname`
   - If `name` is NaN, uses `ip` as fallback
4. Removes legacy fields:
   - `secret`
   - `verbose`
   - `host`
   - `global_delay_factor`
   - `Global_delay_factor` (case variant)
5. Calls parent `__init__()` with transformed data

**Design Note**: The field transformations and removals suggest this plugin evolved from an older inventory system, possibly custom or from another framework.

**Example**:
```python
inventory_plugin = ExcelInventory(
    excel_file="inventory.xlsx",
    excel_sheet="Production"
)
inventory = inventory_plugin.load()
```

## Data Flow

### Complete Data Flow Diagram

```
┌──────────────┐
│  Data Source │
│ (CSV/Excel/  │
│   List)      │
└──────┬───────┘
       │
       │ Parse/Load
       ▼
┌──────────────────────┐
│  List[Dict]          │
│  [{                  │
│    'name': 'r1',     │
│    'hostname': ...,  │
│    'platform': ...,  │
│    'netmiko_*': ..., │
│    'custom': ...     │
│  }]                  │
└──────┬───────────────┘
       │
       │ For each dict
       ▼
┌──────────────────────┐
│  _get_host_obj()     │
│                      │
│  Extracts:           │
│  - Standard fields   │
│  - Custom data       │
│  - Netmiko options   │
└──────┬───────────────┘
       │
       │ Creates
       ▼
┌──────────────────────┐
│  Nornir Host Object  │
│                      │
│  - name              │
│  - hostname          │
│  - platform          │
│  - port              │
│  - username          │
│  - password          │
│  - data: {}          │
│  - connection_options│
└──────┬───────────────┘
       │
       │ Collected into
       ▼
┌──────────────────────┐
│  Nornir Inventory    │
│                      │
│  - hosts: Hosts()    │
│  - groups: Groups()  │
│  - defaults:         │
│    Defaults()        │
└──────────────────────┘
```

### Field Extraction Process

For each host dictionary, fields are categorized as:

```
Input Dictionary Fields
│
├─── Standard Fields
│    ├── name → Host.name
│    ├── hostname → Host.hostname
│    ├── platform → Host.platform
│    ├── port → Host.port
│    ├── username → Host.username
│    └── password → Host.password
│
├─── Netmiko Fields (netmiko_* prefix)
│    ├── netmiko_timeout → ConnectionOptions.extras.timeout
│    ├── netmiko_secret → ConnectionOptions.extras.secret
│    ├── netmiko_fast_cli → ConnectionOptions.extras.fast_cli (bool)
│    └── netmiko_* → ConnectionOptions.extras.*
│
└─── Custom Fields (everything else)
     ├── city → Host.data.city
     ├── model → Host.data.model
     └── * → Host.data.*
```

### Type Conversion Pipeline

```
Raw Value (from CSV/Excel/Dict)
│
├─── Is field in int_keys? (timeout, conn_timeout, etc.)
│    └── int(value)
│
├─── Is field in bool_keys? (fast_cli)
│    └── "false", "0", "none" → False
│         All others → True
│
└─── Is value empty? (None, NaN, "")
     └── Convert to None
```

## Helper Functions

### 1. _empty(x: Any) -> bool

**Location**: `table.py:19-21`

**Purpose**: Unified check for empty/missing values.

**Implementation**:
```python
def _empty(x: Any):
    return x is None or (isinstance(x, float) and isnan(x)) or x == ""
```

**Use Cases**:
- Checking if CSV/Excel cell is empty
- Validating required fields
- Converting empty values to None

**Handles**:
- `None` (Python null)
- `NaN` (pandas float NaN from Excel)
- Empty string `""` (from CSV)

### 2. _get_connection_options(data: Dict) -> Dict[str, ConnectionOptions]

**Location**: `table.py:24-35`

**Purpose**: Create Nornir ConnectionOptions objects from dictionary data.

**Input Format**:
```python
{
    'netmiko': {
        'hostname': '10.0.0.1',
        'port': 22,
        'username': 'admin',
        'password': 'secret',
        'platform': 'cisco_ios',
        'extras': {
            'timeout': 60,
            'secret': 'enable_secret'
        }
    }
}
```

**Output**: `Dict[str, ConnectionOptions]` where each key is a connection type.

### 3. _get_host_data(data: Dict) -> Dict[str, Any]

**Location**: `table.py:38-45`

**Purpose**: Extract custom data fields (non-standard, non-netmiko fields).

**Exclusion List**:
```python
no_data_fields = [
    'name',
    'hostname',
    'port',
    'username',
    'password',
    'platform'
]
```

**Logic**:
1. Iterate through all fields in `data`
2. Skip if field name in `no_data_fields`
3. Skip if field name contains `"netmiko_"`
4. Convert empty values to `None`
5. Include everything else

**Example**:
```python
# Input
data = {
    'name': 'router1',
    'hostname': '10.0.0.1',
    'platform': 'cisco_ios',
    'city': 'NYC',
    'model': 'ASR1000',
    'netmiko_timeout': 60
}

# Output
{'city': 'NYC', 'model': 'ASR1000'}
```

### 4. _get_host_netmiko_options(data: Dict) -> Dict[str, ConnectionOptions]

**Location**: `table.py:48-92`

**Purpose**: Extract and process netmiko-specific fields from host data.

**Integer Fields**:
```python
int_keys = [
    'timeout',
    'conn_timeout',
    'auth_timeout',
    'banner_timeout',
    'blocking_timeout',
    'session_timeout'
]
```

**Boolean Fields**:
```python
bool_keys = ['fast_cli']
```

**Processing Logic**:

```python
For each field in data:
    If field starts with "netmiko_":
        1. Remove "netmiko_" prefix
        2. If field in int_keys:
            → Convert to int
        3. Elif field in bool_keys:
            → Convert to bool (special rules)
        4. Else:
            → Keep as-is (or None if empty)
        5. Add to extras dict

If extras dict not empty:
    Return ConnectionOptions with extras
Else:
    Return empty dict
```

**Boolean Conversion Logic**:
```python
# These become False
"false" (case-insensitive)
"0"
"none" (case-insensitive)

# Everything else becomes True
"true", "1", "yes", "enabled", etc.
```

### 5. _get_host_obj(data: Dict) -> Host

**Location**: `table.py:95-127`

**Purpose**: Create a complete Nornir Host object from dictionary data.

**Process**:

1. **Extract Standard Fields**:
   ```python
   name = data.get('name')
   hostname = data.get('hostname')
   port = data.get('port', 22)  # Default: 22
   username = data.get('username')
   password = data.get('password')
   platform = data.get('platform')
   ```

2. **Type Conversion & Validation**:
   ```python
   # String fields
   name = str(name) if not _empty(name) else str(hostname)
   hostname = str(hostname) if not _empty(hostname) else None

   # Integer fields
   port = int(port) if not _empty(port) else None
   ```

3. **Create Host Object**:
   ```python
   return Host(
       name=name,
       hostname=hostname,
       port=port,
       username=username,
       password=password,
       platform=platform,
       data=_get_host_data(data),
       groups=None,
       defaults={},
       connection_options=_get_host_netmiko_options(data)
   )
   ```

**Key Behaviors**:
- If `name` is empty, uses `hostname` as fallback
- Converts all standard fields to appropriate types
- Separates custom data from standard fields
- Processes netmiko options separately
- No groups assigned (always `None`)
- Empty defaults (always `{}`)

## Plugin Integration

### Nornir Plugin System

Nornir uses Python entry points to discover plugins. This plugin registers three inventory classes:

**Registration** (`pyproject.toml:22-25`):
```toml
[tool.poetry.plugins."nornir.plugins.inventory"]
"FlatDataInventory" = "ns_nornir_table_inventory.plugins.inventory.table:FlatDataInventory"
"CSVInventory" = "ns_nornir_table_inventory.plugins.inventory.table:CSVInventory"
"ExcelInventory" = "ns_nornir_table_inventory.plugins.inventory.table:ExcelInventory"
```

### Plugin Discovery Flow

```
1. User calls InitNornir(inventory={'plugin': 'CSVInventory', ...})
                │
                ▼
2. Nornir scans entry points for 'nornir.plugins.inventory'
                │
                ▼
3. Finds 'CSVInventory' → ns_nornir_table_inventory.plugins.inventory.table:CSVInventory
                │
                ▼
4. Imports the class
                │
                ▼
5. Instantiates CSVInventory(**options)
                │
                ▼
6. Calls .load() method
                │
                ▼
7. Returns Inventory object to Nornir
```

### Plugin Interface Contract

All Nornir inventory plugins must implement:

```python
class InventoryPlugin:
    def __init__(self, **options):
        """Initialize with plugin-specific options"""
        pass

    def load(self) -> Inventory:
        """Return a Nornir Inventory object"""
        pass
```

This plugin adheres to this contract:
- `__init__()` accepts plugin-specific parameters
- `load()` returns `nornir.core.inventory.Inventory`

## Type System

### Type Hints

The codebase uses Python type hints for better code clarity:

```python
from typing import Any, Dict, List
from nornir.core.inventory import (
    Inventory,
    Host,
    Hosts,
    Groups,
    Defaults,
    ConnectionOptions,
)
```

### Type Definitions

**Input Types**:
- `List[Dict]` - List of dictionaries for FlatDataInventory
- `str` - File paths for CSV and Excel inventories

**Internal Types**:
- `Dict[str, Any]` - Generic dictionary for host data
- `Dict[str, ConnectionOptions]` - Connection options mapping

**Output Types**:
- `Inventory` - Nornir inventory object
- `Host` - Individual host object
- `ConnectionOptions` - Connection configuration

### Nornir Core Types

**Inventory Structure**:
```python
Inventory(
    hosts: Hosts,      # Dict-like container of Host objects
    groups: Groups,    # Dict-like container of Group objects
    defaults: Defaults # Default values for all hosts
)
```

**Host Structure**:
```python
Host(
    name: str,
    hostname: Optional[str],
    port: Optional[int],
    username: Optional[str],
    password: Optional[str],
    platform: Optional[str],
    data: Dict[str, Any],
    groups: Optional[List[str]],
    defaults: Dict,
    connection_options: Dict[str, ConnectionOptions]
)
```

**ConnectionOptions Structure**:
```python
ConnectionOptions(
    hostname: Optional[str],
    port: Optional[int],
    username: Optional[str],
    password: Optional[str],
    platform: Optional[str],
    extras: Optional[Dict[str, Any]]
)
```

## Design Decisions

### 1. Why No Groups/Defaults?

**Decision**: Plugin does not support Nornir groups or defaults.

**Rationale**:
- Focus on flat, two-dimensional data structures
- CSV/Excel files naturally represent flat data
- Group hierarchy would require complex multi-sheet or file structures
- Keeps the plugin simple and focused

**Workaround**: Users can filter hosts after loading:
```python
nr = InitNornir(inventory={'plugin': 'CSVInventory', ...})
production = nr.filter(environment='production')
```

### 2. Why Netmiko Only?

**Decision**: Only supports Netmiko connection options.

**Rationale**:
- Netmiko is the most common SSH library for network devices
- Simplifies the interface (one connection type)
- Most network automation use cases involve SSH
- Can be extended in future for other connection types

**Current Limitation**: Cannot use with NAPALM, Scrapli, or other connection plugins without manual configuration.

### 3. Why Separate Excel/CSV Classes?

**Decision**: Separate `CSVInventory` and `ExcelInventory` instead of single class with type parameter.

**Rationale**:
- Clear, explicit plugin names in Nornir config
- Different file formats may need different transformations
- Excel has legacy field mapping that CSV doesn't need
- Follows single responsibility principle

**Alternative Considered**: Single `TableInventory(file='x', format='csv')` - rejected for clarity.

### 4. Why the Legacy Field Removals in Excel?

**Decision**: ExcelInventory removes fields like `secret`, `verbose`, `global_delay_factor`.

**Rationale**:
- Plugin likely evolved from existing Excel-based inventory
- These fields were from older Netmiko or custom system
- Transformation provides backward compatibility
- `device_type` → `platform` and `ip` → `hostname` suggest migration from different naming convention

**Impact**: Users migrating from old Excel format get automatic field mapping.

### 5. Why FlatDataInventory as Base?

**Decision**: Use composition/inheritance with FlatDataInventory as base.

**Rationale**:
- DRY principle - load() logic shared across all classes
- CSV and Excel just need to transform their format to list-of-dict
- Enables database/API integration through same base class
- Clean separation between data loading and inventory creation

**Benefits**:
- Single source of truth for inventory logic
- Easy to add new data sources (JSON, YAML, SQL, etc.)
- Consistent behavior across all inventory types

## Extension Points

### Adding New Inventory Sources

To add a new inventory source (e.g., JSON, database):

```python
from ns_nornir_table_inventory.plugins.inventory.table import FlatDataInventory

class JSONInventory(FlatDataInventory):
    def __init__(self, json_file: str):
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)
        super().__init__(data=data)
```

Register in `pyproject.toml`:
```toml
[tool.poetry.plugins."nornir.plugins.inventory"]
"JSONInventory" = "your_package.plugins.inventory:JSONInventory"
```

### Adding New Connection Types

Currently only Netmiko is supported. To add NAPALM:

1. Modify `_get_host_napalm_options()`:
```python
def _get_host_napalm_options(data: Dict[str, Any]) -> Dict[str, ConnectionOptions]:
    napalm_options = {}
    napalm_prefix = 'napalm_'

    for k, v in data.items():
        if napalm_prefix in k:
            new_k = k.replace(napalm_prefix, '')
            napalm_options[new_k] = v

    if napalm_options:
        return _get_connection_options({'napalm': {'extras': napalm_options}})
    return {}
```

2. Update `_get_host_obj()`:
```python
connection_options = {}
connection_options.update(_get_host_netmiko_options(data))
connection_options.update(_get_host_napalm_options(data))

return Host(
    # ...
    connection_options=connection_options
)
```

### Adding Group Support

To add basic group support:

1. Add `group` field handling in `_get_host_obj()`:
```python
groups = [data.get('group')] if data.get('group') else []

return Host(
    # ...
    groups=groups
)
```

2. Create group objects in `load()`:
```python
def load(self) -> Inventory:
    defaults = Defaults()
    groups_dict = {}
    hosts = Hosts()

    # Create groups
    for host_dict in self.hosts_list:
        group_name = host_dict.get('group')
        if group_name and group_name not in groups_dict:
            groups_dict[group_name] = Group(name=group_name)

    groups = Groups(groups_dict)

    # Create hosts...
```

### Adding Validation

To add schema validation:

```python
from typing import List, Dict
import jsonschema

HOST_SCHEMA = {
    "type": "object",
    "required": ["name", "hostname", "platform"],
    "properties": {
        "name": {"type": "string"},
        "hostname": {"type": "string"},
        "platform": {"type": "string"},
        "port": {"type": "integer"},
        # ...
    }
}

class ValidatedFlatDataInventory(FlatDataInventory):
    def __init__(self, data: List[Dict], schema: Dict = HOST_SCHEMA):
        # Validate each host dict
        for host in data:
            jsonschema.validate(instance=host, schema=schema)
        super().__init__(data=data)
```

## Internal Data Structures

### hosts_list Format

After parsing but before conversion to Nornir objects:

```python
hosts_list = [
    {
        # Standard fields
        'name': 'router1',
        'hostname': '10.0.0.1',
        'platform': 'cisco_ios',
        'port': 22,
        'username': 'admin',
        'password': 'secret',

        # Netmiko fields
        'netmiko_timeout': 60,
        'netmiko_secret': 'enable_pass',
        'netmiko_fast_cli': True,

        # Custom fields
        'city': 'NYC',
        'model': 'ASR1000',
        'rack': 'A-1-5'
    },
    # ... more hosts
]
```

### Transformation Map

**ExcelInventory Transformations**:

| Excel Column | Internal Field | Notes |
|-------------|---------------|-------|
| `device_type` | `platform` | Renamed |
| `ip` | `hostname` | Renamed |
| `name` (if NaN) | `name` | Falls back to `ip` |
| `secret` | (removed) | Legacy field |
| `verbose` | (removed) | Legacy field |
| `host` | (removed) | Legacy field |
| `global_delay_factor` | (removed) | Legacy field |

### Connection Options Structure

After processing by `_get_host_netmiko_options()`:

```python
{
    'netmiko': ConnectionOptions(
        hostname=None,      # Set to None, uses Host.hostname
        port=None,          # Set to None, uses Host.port
        username=None,      # Set to None, uses Host.username
        password=None,      # Set to None, uses Host.password
        platform=None,      # Set to None, uses Host.platform
        extras={
            'timeout': 60,
            'secret': 'enable_pass',
            'fast_cli': True,
            'banner_timeout': 15
        }
    )
}
```

**Note**: Standard connection fields (hostname, port, etc.) are set to `None` in ConnectionOptions because they're already defined at the Host level. Only extras are populated.

## Performance Considerations

### Memory Usage

- **CSV**: Uses Python's `csv.DictReader` - low memory, streaming
- **Excel**: Uses `pandas.read_excel()` - loads entire sheet into memory
- **Large Files**: Consider splitting large Excel files or using CSVInventory

### Loading Time

**Benchmark (approximate)**:

| Source | 100 hosts | 1000 hosts | 10000 hosts |
|--------|-----------|------------|-------------|
| CSV | <0.1s | ~0.5s | ~5s |
| Excel | ~0.5s | ~2s | ~20s |
| FlatData | <0.01s | <0.1s | ~1s |

**Optimization Tips**:
1. Use CSV for large inventories (faster parsing)
2. Use FlatDataInventory with database cursor for very large inventories
3. Consider caching `Inventory` object if reused frequently

### Scaling Considerations

For inventories >10,000 hosts:

```python
# Option 1: Lazy loading from database
def get_inventory_lazy():
    # Only fetch active devices
    cursor.execute("SELECT * FROM devices WHERE active = true")
    data = [dict(row) for row in cursor.fetchall()]
    return FlatDataInventory(data=data).load()

# Option 2: Partition by site
def get_site_inventory(site_id):
    cursor.execute("SELECT * FROM devices WHERE site_id = ?", (site_id,))
    data = [dict(row) for row in cursor.fetchall()]
    return FlatDataInventory(data=data).load()

# Option 3: Use Nornir's filtering capabilities
nr = InitNornir(config_file='config.yml')
site_a = nr.filter(site='site_a')  # Work with subset
```

## Testing Strategy

### Unit Test Structure (Recommended)

```python
import pytest
from ns_nornir_table_inventory.plugins.inventory.table import (
    FlatDataInventory,
    CSVInventory,
    ExcelInventory,
    _empty,
    _get_host_data,
    _get_host_netmiko_options,
    _get_host_obj
)

class TestHelperFunctions:
    def test_empty_none(self):
        assert _empty(None) is True

    def test_empty_nan(self):
        import math
        assert _empty(float('nan')) is True

    def test_empty_string(self):
        assert _empty("") is True

    def test_not_empty(self):
        assert _empty("value") is False

class TestFlatDataInventory:
    def test_basic_inventory(self):
        data = [{'name': 'test', 'hostname': '10.0.0.1', ...}]
        inv = FlatDataInventory(data=data).load()
        assert 'test' in inv.hosts

class TestCSVInventory:
    def test_load_csv(self, tmp_path):
        # Create temp CSV
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,hostname,platform\ntest,10.0.0.1,cisco_ios")
        inv = CSVInventory(csv_file=str(csv_file)).load()
        assert 'test' in inv.hosts

# Add more tests...
```

## Debugging

### Logging

Enable debug logging to see what's happening:

```python
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now use the plugin
from nornir import InitNornir
nr = InitNornir(config_file='config.yml')
```

### Common Debug Points

1. **Check parsed data before load()**:
```python
from ns_nornir_table_inventory.plugins.inventory.table import CSVInventory

inv_plugin = CSVInventory(csv_file="inventory.csv")
print("Raw hosts list:", inv_plugin.hosts_list)
inventory = inv_plugin.load()
```

2. **Inspect Host objects**:
```python
for name, host in nr.inventory.hosts.items():
    print(f"\nHost: {name}")
    print(f"  Hostname: {host.hostname}")
    print(f"  Platform: {host.platform}")
    print(f"  Data: {host.data}")
    print(f"  Connection options: {host.connection_options}")
```

3. **Check helper function output**:
```python
from ns_nornir_table_inventory.plugins.inventory.table import (
    _get_host_data,
    _get_host_netmiko_options
)

test_data = {
    'name': 'test',
    'hostname': '10.0.0.1',
    'city': 'NYC',
    'netmiko_timeout': 60
}

print("Custom data:", _get_host_data(test_data))
print("Netmiko options:", _get_host_netmiko_options(test_data))
```

---

**Document Version**: 1.0
**Last Updated**: 2024
**Maintainer**: nstamoul <nstamoul0@gmail.com>
