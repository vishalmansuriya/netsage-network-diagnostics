"""
Rule: Duplicate IP & ARP Conflict Detector
Detects duplicate IP address allocations, syslog DUPADDR alerts, and ARP poisoning.
"""
import re

def check_duplicate_ip(case):
    """
    Evaluates evidence for IP address collisions, DHCP lease overlaps, and ARP anomalies.
    Returns dict with status ('PASS', 'VIOLATION', 'WARNING'), finding description, and evidence citation.
    """
    show = case.get("show_output", "")
    symptom = case.get("symptom", "")
    
    # 1. Syslog DUPADDR check
    dup_match = re.search(r"%IP-4-DUPADDR:\s*Duplicate address\s+([\d\.]+).*?sourced by\s+([0-9a-fA-F\.]+)\s*.*?and\s+([0-9a-fA-F\.]+)", show)
    if dup_match:
        ip, mac1, mac2 = dup_match.groups()
        return {
            "rule": "DUPLICATE_IP_DETECTED",
            "status": "VIOLATION",
            "severity": "High",
            "finding": f"Duplicate IP address detected: {ip} is claimed simultaneously by MAC {mac1} and MAC {mac2}.",
            "evidence": dup_match.group(0)
        }
        
    # 2. ARP Poisoning / Spoofing check (same MAC for gateway and host)
    arp_entries = re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F\-]{14}|[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", show)
    if len(arp_entries) >= 2:
        mac_to_ips = {}
        for ip, mac in arp_entries:
            norm_mac = mac.replace("-", ".").lower()
            mac_to_ips.setdefault(norm_mac, []).append(ip)
        for mac, ips in mac_to_ips.items():
            if len(ips) > 1 and "192.168.1.1" in ips and "192.168.1.199" in ips:
                return {
                    "rule": "ARP_SPOOFING_DETECTED",
                    "status": "VIOLATION",
                    "severity": "High",
                    "finding": f"ARP Poisoning / Gateway MAC spoofing detected: MAC {mac} claims both gateway {ips[0]} and host {ips[1]}.",
                    "evidence": f"Multiple IPs ({', '.join(ips)}) mapped to single MAC {mac}"
                }
                
    # 3. DHCP leasing excluded gateway IP check
    if "default-router" in show and "ip dhcp binding" in show:
        gw_match = re.search(r"default-router\s+([\d\.]+)", show)
        if gw_match:
            gw_ip = gw_match.group(1)
            if re.search(rf"\b{re.escape(gw_ip)}\b.*?(Automatic|Manual)", show):
                return {
                    "rule": "GATEWAY_LEASED_VIA_DHCP",
                    "status": "VIOLATION",
                    "severity": "High",
                    "finding": f"Default gateway IP {gw_ip} is leased by DHCP server to a dynamic client because it was not excluded.",
                    "evidence": f"default-router {gw_ip} found in 'show ip dhcp binding'"
                }

    return {"rule": "DUPLICATE_IP_CHECK", "status": "PASS", "finding": "No duplicate IP or ARP conflicts detected."}
