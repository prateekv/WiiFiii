"""
sensor-backend/device_scanner.py
───────────────────────────────
Standalone live network scanner.
Detects current WiFi network and scans for all connected devices.
Refreshes every 5 seconds in a live terminal dashboard.
"""

import os
import time
import socket
import logging
import subprocess
import ipaddress
import concurrent.futures
from dataclasses import dataclass

# Disable default logging to keep the terminal clean
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

@dataclass
class Device:
    ip: str
    mac: str
    hostname: str

@dataclass
class NetworkInfo:
    ssid: str
    gateway_ip: str
    local_ip: str
    subnet_cidr: str

def clear_terminal():
    """Clears the terminal screen for a live dashboard effect."""
    os.system('cls' if os.name == 'nt' else 'clear')

def check_admin_privileges() -> bool:
    """Checks if the script is running with Administrator/Root privileges."""
    try:
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False

def get_network_info() -> NetworkInfo:
    """Detects the current active network (SSID, Gateway, IP, Subnet)."""
    # 1. Get Gateway and Local IP via ipconfig / route
    gateway_ip = "Unknown"
    local_ip = "Unknown"
    
    if os.name == 'nt':
        try:
            # Parse route print for default gateway
            route_out = subprocess.check_output("route print -4 0.0.0.0", shell=True, text=True)
            for line in route_out.splitlines():
                if "0.0.0.0" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        gateway_ip = parts[2]
                        local_ip = parts[3]
                        break
        except Exception:
            pass

    # Fallback/Linux (using socket)
    if gateway_ip == "Unknown":
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            # Approximation for gateway if route print fails
            gateway_ip = local_ip.rsplit('.', 1)[0] + '.1'
        except Exception:
            pass

    # 2. Get SSID via netsh (Windows)
    ssid = "Unknown"
    if os.name == 'nt':
        try:
            netsh_out = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True)
            for line in netsh_out.splitlines():
                if " SSID" in line and "BSSID" not in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        ssid = parts[1].strip()
                        break
        except Exception:
            pass

    # 3. Calculate subnet CIDR assuming standard /24 for home networks
    subnet = "Unknown"
    if local_ip != "Unknown":
        try:
            net = ipaddress.IPv4Interface(f"{local_ip}/24")
            subnet = str(net.network)
        except Exception:
            pass

    return NetworkInfo(ssid=ssid, gateway_ip=gateway_ip, local_ip=local_ip, subnet_cidr=subnet)

def resolve_hostname(ip: str) -> str:
    """Attempts to find the hostname for an IP address."""
    try:
        host = socket.gethostbyaddr(ip)[0]
        return host
    except Exception:
        return "Unknown"

def scan_network_scapy(subnet: str) -> list[Device]:
    """Scans the network using Scapy. Requires Admin privileges."""
    try:
        # Import inside function so failure doesn't crash the script early
        from scapy.all import ARP, Ether, srp
    except ImportError:
        raise ImportError("Scapy is not installed. Run: pip install scapy")

    devices = []
    # Create ARP request
    arp = ARP(pdst=subnet)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp

    # Send and receive packets
    result = srp(packet, timeout=2, verbose=0)[0]
    
    for sent, received in result:
        devices.append(Device(
            ip=received.psrc,
            mac=received.hwsrc,
            hostname=resolve_hostname(received.psrc)
        ))
    return devices

def scan_network_fallback(subnet: str) -> list[Device]:
    """Scans the network using a ping sweep and reading the OS ARP cache."""
    devices = []
    
    # 1. Ping sweep to populate ARP cache
    def ping(ip):
        cmd = ["ping", "-n", "1", "-w", "200", str(ip)] if os.name == 'nt' else ["ping", "-c", "1", "-W", "1", str(ip)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        network = ipaddress.IPv4Network(subnet, strict=False)
        # Ping the first 50 addresses for speed, or all if you prefer. 
        # We'll just do the whole /24 but aggressively concurrent
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(ping, list(network.hosts()))
    except Exception:
        pass

    # 2. Read ARP cache
    try:
        arp_out = subprocess.check_output("arp -a", shell=True, text=True)
        for line in arp_out.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                mac = parts[1].replace('-', ':')
                
                # Basic validation
                if ip.count('.') == 3 and len(mac) == 17:
                    # Filter out broadcast/multicast
                    if ip.endswith(".255") or ip.startswith("224.") or ip.startswith("239."):
                        continue
                    
                    devices.append(Device(
                        ip=ip,
                        mac=mac,
                        hostname=resolve_hostname(ip)
                    ))
    except Exception:
        pass
        
    return devices

def main():
    print("Checking privileges...")
    is_admin = check_admin_privileges()
    
    while True:
        clear_terminal()
        print("="*60)
        print(" 🌐 LIVE WIFI NETWORK SCANNER ")
        print("="*60)

        # Detect Network
        print("\nDetecting network...")
        net_info = get_network_info()
        print(f"Network Name (SSID) : {net_info.ssid}")
        print(f"Router Gateway IP   : {net_info.gateway_ip}")
        print(f"Your Laptop IP      : {net_info.local_ip}")
        print(f"Scanning Subnet     : {net_info.subnet_cidr}")
        print("-" * 60)

        if net_info.subnet_cidr == "Unknown":
            print("ERROR: Could not detect network subnet. Are you connected to WiFi?")
            time.sleep(5)
            continue

        # Determine Scan Method based on privileges
        devices = []
        if is_admin:
            print("Mode: ACTIVE SCAN (Administrator Privileges Detected)")
            print("Scanning with Scapy for highest accuracy...")
            try:
                devices = scan_network_scapy(net_info.subnet_cidr)
            except ImportError as e:
                print(f"\n[ERROR] {e}")
                print("Falling back to standard scan...")
                devices = scan_network_fallback(net_info.subnet_cidr)
        else:
            print("Mode: PASSIVE SCAN (Standard Privileges)")
            print("Scanning via ARP cache. Note: Some silent devices may be missed.")
            print("👉 Tip: Run this terminal as Administrator for a more accurate active scan.")
            devices = scan_network_fallback(net_info.subnet_cidr)

        # Print Results
        print("\n" + "="*60)
        print(f" CONNECTED DEVICES FOUND: {len(devices)}")
        print("="*60)
        print(f"{'IP ADDRESS':<16} | {'MAC ADDRESS':<18} | {'HOSTNAME / DEVICE NAME'}")
        print("-" * 60)
        
        if not devices:
            print("No other devices found on this network.")
        else:
            for d in sorted(devices, key=lambda x: tuple(map(int, x.ip.split('.')))):
                # Highlight the router and the host machine
                tag = ""
                if d.ip == net_info.gateway_ip:
                    tag = " (ROUTER)"
                elif d.ip == net_info.local_ip:
                    tag = " (THIS LAPTOP)"
                
                print(f"{d.ip:<16} | {d.mac:<18} | {d.hostname}{tag}")

        print("\n(Refreshing automatically in 5 seconds... Press Ctrl+C to stop)")
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScanner stopped by user. Goodbye!")
