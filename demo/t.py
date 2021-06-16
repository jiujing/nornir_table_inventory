from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir.core.plugins.inventory import InventoryPluginRegister

from plugins.inventory.table import CSVInventory

InventoryPluginRegister.register("CSVInventory", CSVInventory)

runner = {
    "plugin": "threaded",
    "options": {
        "num_workers": 100,
    },
}
inventory = {
    "plugin": "CSVInventory",
    "options": {
        "csv_file": "inventory.csv",
    },
}

nr = InitNornir(runner=runner, inventory=inventory)
bj_devs = nr.filter(city='bj')
results = bj_devs.run(task=netmiko_send_command, command_string='show version')
print_result(results)
