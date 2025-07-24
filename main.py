from network_change_detector import NetworkChangeDetector

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
