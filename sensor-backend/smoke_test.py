"""Quick smoke test for network_scanner.py — run with: python smoke_test.py"""
from network_scanner import get_network_info, read_arp_cache

info = get_network_info()
print(f"SSID:       {info.ssid}")
print(f"Signal:     {info.signal_pct}")
print(f"Gateway:    {info.gateway_ip}")
print(f"Local IP:   {info.local_ip}")
print(f"Subnet:     {info.subnet_mask}")
print(f"CIDR:       {info.subnet_cidr()}")
print()
devices = read_arp_cache()
print(f"ARP cache ({len(devices)} devices):")
for d in devices:
    label = d.hostname if d.hostname else "(no hostname)"
    print(f"  {d.ip:<18} {d.mac:<20} {label}")
