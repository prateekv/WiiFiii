"""
sensor-backend/network_scanner.py
──────────────────────────────────
Detects current WiFi network info and ARP-scans the subnet for devices.

Scan strategy (auto-selected):
  1. Scapy full ARP scan   — best results, needs Npcap + run as Administrator
  2. Ping sweep + arp -a   — good results, NO admin needed (default fallback)

Both paths return the same Device dataclass so the server code is identical.

Notes:
  - Uses netsh wlan + ipconfig for network info (no netifaces.gateways needed)
  - netifaces2 on Python 3.14 lacks gateways(); we parse ipconfig instead
"""

import concurrent.futures
import ipaddress
import logging
import re
import socket
import subprocess
import time
from dataclasses import dataclass, field
from typing import List, Optional

log = logging.getLogger(__name__)

# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class Device:
    ip: str
    mac: str
    hostname: str = ""
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname or self.ip,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


@dataclass
class NetworkInfo:
    ssid: str = "Unknown"
    bssid: str = ""
    gateway_ip: str = ""
    local_ip: str = ""
    subnet_mask: str = "255.255.255.0"
    signal_pct: str = ""
    interface: str = ""

    def subnet_cidr(self) -> str:
        """Return e.g. '192.168.1.0/24' from gateway + mask."""
        try:
            net = ipaddress.IPv4Network(
                f"{self.gateway_ip}/{self.subnet_mask}", strict=False
            )
            return str(net)
        except Exception:
            parts = self.gateway_ip.rsplit(".", 1)
            return f"{parts[0]}.0/24" if len(parts) == 2 else "192.168.1.0/24"

    def to_dict(self) -> dict:
        return {
            "ssid": self.ssid,
            "gateway_ip": self.gateway_ip,
            "local_ip": self.local_ip,
            "signal_pct": self.signal_pct,
            "subnet_cidr": self.subnet_cidr(),
        }


# ── WiFi / network info ────────────────────────────────────────────────────────

def get_network_info() -> NetworkInfo:
    """
    Returns current WiFi SSID + gateway IP + local IP.
    Uses netsh wlan (SSID/signal) + ipconfig (gateway/local IP) on Windows.
    No admin rights needed.
    """
    info = NetworkInfo()

    # ── Step 1: WiFi details via netsh wlan ─────────────────────────────────
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            stripped = line.strip()
            # netsh field names look like: "   SSID                   : MyNetwork"
            # or:                          "   SSID                   : MyNetwork"
            if re.match(r"SSID\b", stripped) and "BSSID" not in stripped:
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    info.ssid = parts[1].strip()
            elif stripped.startswith("BSSID"):
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    info.bssid = parts[1].strip()
            elif stripped.startswith("Signal"):
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    info.signal_pct = parts[1].strip()
    except Exception as e:
        log.warning(f"netsh wlan failed: {e}")

    # ── Step 1b: SSID fallback — parse ipconfig adapter name ─────────────────
    # When netsh needs Location Services, the adapter description in ipconfig
    # usually contains the SSID or network name for WiFi adapters.
    if info.ssid == "Unknown":
        try:
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                # Adapter headers look like: "Wireless LAN adapter Wi-Fi:"
                # or "Ethernet adapter Ethernet:"
                if re.match(r"^\S.*adapter.*:", line, re.IGNORECASE):
                    # Keep looking — we'll find a WiFi one
                    pass
                # Network name from 'Connection-specific DNS Suffix' or just adapter label
                if re.search(r"wi.?fi|wireless|wlan", line, re.IGNORECASE):
                    # Extract the part after "adapter"
                    m = re.search(r"adapter\s+(.+?):", line, re.IGNORECASE)
                    if m:
                        name = m.group(1).strip()
                        if name.lower() not in ("wi-fi", "wireless", "wlan"):
                            info.ssid = name
                        else:
                            info.ssid = "Wi-Fi"  # at least say it's WiFi
                        break
        except Exception:
            pass


    # ── Step 2: Gateway + local IP via ipconfig ──────────────────────────────
    # ipconfig always works without admin on Windows
    try:
        result = subprocess.run(
            ["ipconfig"], capture_output=True, text=True, timeout=5
        )
        _parse_ipconfig(result.stdout, info)
    except Exception as e:
        log.warning(f"ipconfig failed: {e}")

    # ── Step 3: Fallback gateway via 'route print 0.0.0.0' ──────────────────
    if not info.gateway_ip:
        try:
            result = subprocess.run(
                ["route", "print", "0.0.0.0"],
                capture_output=True, text=True, timeout=5
            )
            # Find line: 0.0.0.0  0.0.0.0  <gateway>  <local_ip>  <metric>
            pattern = re.compile(
                r"\s+0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)"
            )
            for line in result.stdout.splitlines():
                m = pattern.match(line)
                if m:
                    info.gateway_ip = m.group(1)
                    if not info.local_ip:
                        info.local_ip = m.group(2)
                    break
        except Exception as e:
            log.warning(f"route print failed: {e}")

    return info


def _parse_ipconfig(output: str, info: NetworkInfo) -> None:
    """
    Parse `ipconfig` output to extract IPv4 address, subnet mask, gateway.
    Prefers adapters whose names suggest WiFi (Wireless, Wi-Fi, WLAN).
    """
    # Split into adapter blocks
    blocks = re.split(r"^(?=\S)", output, flags=re.MULTILINE)
    wifi_block = None
    fallback_block = None

    for block in blocks:
        is_wifi = bool(re.search(r"wi.?fi|wireless|wlan|802\.11", block, re.IGNORECASE))
        has_ip  = bool(re.search(r"IPv4 Address", block))
        has_gw  = bool(re.search(r"Default Gateway", block))
        if is_wifi and has_ip and has_gw:
            wifi_block = block
            break
        if has_ip and has_gw and not fallback_block:
            fallback_block = block

    chosen = wifi_block or fallback_block
    if not chosen:
        return

    for line in chosen.splitlines():
        stripped = line.strip()
        if re.match(r"IPv4 Address", stripped) and not info.local_ip:
            # "IPv4 Address. . . . . . . . . . . : 192.168.1.50"
            info.local_ip = stripped.split(":", 1)[-1].strip().rstrip("(Preferred)")
        elif re.match(r"Subnet Mask", stripped) and info.subnet_mask == "255.255.255.0":
            info.subnet_mask = stripped.split(":", 1)[-1].strip()
        if re.match(r"Default Gateway", stripped) and not info.gateway_ip:
            gw = stripped.split(":", 1)[-1].strip()
            # Skip IPv6 link-local addresses (start with 'fe80')
            if gw and not gw.lower().startswith("fe80"):
                info.gateway_ip = gw


# ── Hostname resolution ────────────────────────────────────────────────────────

def resolve_hostname(ip: str, timeout: float = 0.5) -> str:
    """Reverse-DNS lookup with timeout. Returns empty string on failure."""
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        name = socket.gethostbyaddr(ip)[0]
        return name
    except Exception:
        return ""
    finally:
        socket.setdefaulttimeout(old_timeout)


# ── Ping sweep (populates ARP cache without admin) ────────────────────────────

def _ping_one(ip: str) -> None:
    """Fire-and-forget ping to populate ARP cache."""
    try:
        subprocess.run(
            ["ping", "-n", "1", "-w", "300", ip],
            capture_output=True, timeout=1
        )
    except Exception:
        pass


def ping_sweep(cidr: str, max_workers: int = 80) -> None:
    """
    Pings every host in the subnet concurrently to warm the ARP cache.
    No admin needed. Runs in ~1-2 seconds for a /24.
    """
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
        hosts = [str(h) for h in network.hosts()]
        if len(hosts) > 510:          # skip if subnet is too large
            log.warning("Subnet >510 hosts — skipping ping sweep")
            return
        log.debug(f"Ping sweep: {len(hosts)} hosts on {cidr}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            pool.map(_ping_one, hosts)
    except Exception as e:
        log.warning(f"Ping sweep error: {e}")


# ── ARP cache reader (arp -a, always works, no admin) ─────────────────────────

_MAC_PATTERN = re.compile(
    r"^\s+([\d.]+)\s+([\da-fA-F-]{17})\s+(dynamic|static)",
    re.IGNORECASE,
)
_SKIP_IPS = re.compile(r"^(224\.|239\.|255\.|0\.)") 
_SKIP_MAC = re.compile(r"^ff:ff:ff:ff:ff:ff$", re.IGNORECASE)


def read_arp_cache() -> List[Device]:
    """Parse output of `arp -a`. Returns Device list. No admin needed."""
    devices = []
    try:
        result = subprocess.run(
            ["arp", "-a"], capture_output=True, text=True, timeout=5
        )
        now = time.time()
        seen_ips = set()
        for line in result.stdout.splitlines():
            m = _MAC_PATTERN.match(line)
            if not m:
                continue
            ip = m.group(1)
            mac = m.group(2).replace("-", ":").lower()
            if _SKIP_IPS.match(ip) or _SKIP_MAC.match(mac) or ip in seen_ips:
                continue
            seen_ips.add(ip)
            hostname = resolve_hostname(ip)
            devices.append(Device(ip=ip, mac=mac, hostname=hostname,
                                  first_seen=now, last_seen=now))
    except Exception as e:
        log.error(f"arp -a failed: {e}")
    return devices


# ── Scapy ARP scan (requires Npcap + Administrator) ───────────────────────────

def scapy_arp_scan(cidr: str) -> Optional[List[Device]]:
    """
    Full ARP scan via Scapy. Returns None if Scapy/Npcap unavailable.
    Run the process as Administrator for this path to work.
    """
    try:
        from scapy.all import ARP, Ether, srp  # type: ignore
        log.info(f"Scapy ARP scan on {cidr}")
        arp_req = ARP(pdst=cidr)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        answered, _ = srp(broadcast / arp_req, timeout=2, verbose=False)
        now = time.time()
        devices = []
        for _, rcv in answered:
            ip = rcv.psrc
            mac = rcv.hwsrc.lower()
            hostname = resolve_hostname(ip)
            devices.append(Device(ip=ip, mac=mac, hostname=hostname,
                                  first_seen=now, last_seen=now))
        return devices
    except Exception as e:
        log.debug(f"Scapy unavailable: {e}")
        return None


# ── Main scan function ─────────────────────────────────────────────────────────

def scan_network(info: NetworkInfo) -> List[Device]:
    """
    Scan the local subnet. Auto-selects best available method.
    Always returns a list (possibly empty on errors).
    """
    if not info.gateway_ip:
        log.warning("No gateway IP — cannot scan")
        return []

    cidr = info.subnet_cidr()

    # Try Scapy first (better results, needs Npcap + admin)
    devices = scapy_arp_scan(cidr)
    if devices is not None:
        log.info(f"Scapy found {len(devices)} devices")
        return _dedupe(devices)

    # Fallback: ping sweep to warm cache, then read arp -a
    log.info("Using ping-sweep + arp -a fallback")
    ping_sweep(cidr)
    devices = read_arp_cache()

    # Filter to only devices in our subnet
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
        devices = [d for d in devices if ipaddress.IPv4Address(d.ip) in network]
    except Exception:
        pass

    log.info(f"arp -a found {len(devices)} devices in {cidr}")
    return _dedupe(devices)


def _dedupe(devices: List[Device]) -> List[Device]:
    """Remove duplicate IPs, keep last seen."""
    seen: dict[str, Device] = {}
    for d in devices:
        seen[d.ip] = d
    return sorted(seen.values(), key=lambda d: ipaddress.IPv4Address(d.ip))
