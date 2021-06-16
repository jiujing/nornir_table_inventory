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
print(nr.hosts)