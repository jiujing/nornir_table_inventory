from nornir import InitNornir


nr = InitNornir(config_file=r'config.yml')
for n,h in nr.inventory.hosts.items():
    print(n, h.dict())