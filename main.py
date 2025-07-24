import platform
import time
import socket
import psutil
import subprocess
import threading
import re

from collections.abc import Callable

class NetworkChangeDetector:
    def __init__(self, on_change: Callable):
        self.on_change = on_change
        self.ip = self._get_current_ip()
        self.all_interface_ips = self._get_all_interface_ips()
        self.interfaces = self._get_active_interfaces()
        self.ssid = self._get_current_ssid()
        self._running = False

    def start_monitoring(self, interval_seconds: int = 2):
        if not self._running:
            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self._monitor, args=(interval_seconds,))
            self._thread.start()
            self._running = True
            print("[NCD] Network monitor started")
            return

        print("[NCD] Already running...")
        
    def stop_monitoring(self):
        if self._running:
            print("[NCD] Network monitor stopping...")
            self._stop_event.set()
            self._thread.join()
            self._running = False
            print("[NCD] Network monitor stopped")
            return

        print("[NCD] Already stopped...")

    def _monitor(self, interval_seconds: int):
        while not self._stop_event.is_set():
            something_changed = False

            current_ip = self._get_current_ip()
            current_interface_ips = self._get_all_interface_ips()
            current_interfaces = self._get_active_interfaces()
            current_ssid = self._get_current_ssid()

            if current_ip != self.ip:
                print(f"[NCD: IP] Change of IP: {self.ip} -> {current_ip}")
                self.ip = current_ip
                something_changed = True

            if current_interface_ips != self.all_interface_ips:
                print(f"[NCD: Interface IPs] Change of some Interface IP: {self.all_interface_ips} -> {current_interface_ips}")
                self.all_interface_ips = current_interface_ips
                something_changed = True

            if current_interfaces != self.interfaces:
                print(f"[NCD: Interface] Change of interfaces: {self.interfaces} -> {current_interfaces}")
                self.interfaces = current_interfaces
                something_changed = True

            if current_ssid != self.ssid:
                print(f"[NCD: Wi-Fi] Change of SSID: {self.ssid} -> {current_ssid}")
                self.ssid = current_ssid
                something_changed = True

            if something_changed:
                self.on_change()

            time.sleep(interval_seconds)

    def _get_current_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

    def _get_all_interface_ips(self):
        results = {}
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface, iface_addrs in addrs.items():
            if not stats.get(iface) or not stats[iface].isup:
                continue

            for addr in iface_addrs:
                if addr.family == socket.AF_INET: # IPv4
                    results[iface] = addr.address

        return results

    def _get_active_interfaces(self):
        stats = psutil.net_if_stats()
        return sorted([iface for iface, stat in stats.items() if stat.isup])

    def _get_ssid_nmcli(self):
        try:
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
                stderr=subprocess.DEVNULL,
            ).decode()
            for line in output.strip().split('\n'):
                if line.startswith("yes:"):
                    return line.split(":")[1]
        except:
            return None

    def _get_ssid_wpa_cli(self):
        try:
            output = subprocess.check_output(["wpa_cli", "status"], stderr=subprocess.DEVNULL).decode()
            for line in output.strip().split('\n'):
                if line.startswith("ssid="):
                    return line.split("=")[1]
        except:
            return None

    def _get_linux_ssid(self):
        ssid = self._get_ssid_nmcli()
        if ssid:
            return ssid

        ssid = self._get_ssid_wpa_cli()
        if ssid:
            return ssid

        try:
            ssid = subprocess.check_output(["iwgetid", "--raw"], stderr=subprocess.DEVNULL).decode().strip()
            if ssid:
                return ssid
        except:
            pass

        return None

    def _get_current_ssid(self):
        system = platform.system()
        try:
            if system == "Linux":
                return self._get_linux_ssid()
            elif system == "Windows":
                output = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
                match = re.search(r'\s*SSID\s*:\s(.+)', output)
                if match:
                    return match.group(1).strip()
        except:
            return None

        return None


def restart_zeroconf():
    print("[ON_CHANGE] Restarting zeroconf...")

network_change_detector = NetworkChangeDetector(on_change=restart_zeroconf)

print("Starting Network Change Detector (NCD)...\n")
network_change_detector.start_monitoring()

while True:
    command = input("\n>>> Enter 'stop' to stop the monitoring...\n")
    if command != "stop":
        print(f"Unknown command: {command}")
    else:
        break

network_change_detector.stop_monitoring()
