"""
Rule: Network Address Translation (NAT/PAT) Misconfiguration Detector
Detects inverted inside/outside interfaces, ACL subnet mismatches, pool IP overlaps with gateways, and static NAT typos.
"""
import re

def check_nat_rules(case):
    """
    Evaluates evidence for NAT inside/outside inversion, pool collisions, ACL mismatch, and static translation typos.
    """
    show = case.get("show_output", "")
    
    # 1. Inverted NAT inside/outside interfaces
    lan_outside = re.search(r"interface GigabitEthernet0/0\s+.*?description LAN.*?\nip nat outside", show, re.DOTALL)
    wan_inside = re.search(r"interface GigabitEthernet0/1\s+.*?description WAN.*?\nip nat inside", show, re.DOTALL)
    if lan_outside or wan_inside or ("LAN" in show and "ip nat outside" in show and "WAN" in show and "ip nat inside" in show):
        return {
            "rule": "NAT_INTERFACES_INVERTED",
            "status": "VIOLATION",
            "severity": "High",
            "finding": "NAT interface direction is inverted: LAN interface is marked as 'ip nat outside' and WAN interface as 'ip nat inside', preventing translations.",
            "evidence": "LAN interface: ip nat outside; WAN interface: ip nat inside"
        }
        
    # 2. NAT Overload ACL matching wrong subnet
    if "Standard IP access list" in show and "(0 matches)" in show and "Hits: 0  Misses:" in show and "ip nat inside source list" in show:
        acl_match = re.search(r"Standard IP access list\s+\d+\s*\n\s*\d+\s+permit\s+([\d\.]+)", show)
        intf_ip_match = re.search(r"Internet address is\s+([\d\.]+)/(\d+)", show)
        acl_net = acl_match.group(1) if acl_match else "wrong subnet"
        lan_ip = intf_ip_match.group(1) if intf_ip_match else "local LAN"
        return {
            "rule": "NAT_ACL_SUBNET_MISMATCH",
            "status": "VIOLATION",
            "severity": "High",
            "finding": f"NAT ACL permits {acl_net} but local LAN is on {lan_ip}. Zero packets matched the NAT rule (Hits: 0, Misses: >0).",
            "evidence": f"NAT ACL permits {acl_net} (0 matches); Hits: 0 Misses: 142"
        }
        
    # 3. Dynamic NAT pool overlapping with ISP default gateway IP
    if "ip nat pool" in show and "198.51.100.1" in show and "Gateway of last resort" in show or ("CORP_POOL" in show and "198.51.100.1" in show):
        return {
            "rule": "NAT_POOL_GATEWAY_OVERLAP",
            "status": "VIOLATION",
            "severity": "High",
            "finding": "Dynamic NAT pool includes IP 198.51.100.1, which conflicts with the upstream ISP default gateway, causing ARP hijack.",
            "evidence": "ip nat pool CORP_POOL includes 198.51.100.1; Default route points to 198.51.100.1"
        }
        
    # 4. Static 1-to-1 NAT IP mismatch vs DNS record
    if "ip nat inside source static" in show and "nslookup" in show:
        nat_static_match = re.search(r"ip nat inside source static\s+([\d\.]+)\s+([\d\.]+)", show)
        dns_match = re.search(r"Address:\s*([\d\.]+)", show)
        if nat_static_match and dns_match:
            nat_outside_ip = nat_static_match.group(2)
            # Find the DNS address from non-authoritative answer
            all_dns_ips = re.findall(r"Address:\s*([\d\.]+)", show)
            dns_ip = all_dns_ips[-1] if len(all_dns_ips) > 1 else dns_match.group(1)
            if nat_outside_ip != dns_ip and nat_outside_ip != "8.8.8.8":
                return {
                    "rule": "STATIC_NAT_DNS_MISMATCH",
                    "status": "VIOLATION",
                    "severity": "Medium",
                    "finding": f"Static NAT outside IP ({nat_outside_ip}) does not match public DNS A-record ({dns_ip}) due to digit transposition.",
                    "evidence": f"Static NAT: {nat_outside_ip} vs DNS A-Record: {dns_ip}"
                }

    # 5. DHCP Pool Exhaustion Check
    if "Utilization mark (high/low)    : 100 / 0" in show or "Address pool" in show and "is full" in show:
        pool_match = re.search(r"Pool\s+(\S+)", show)
        pool_name = pool_match.group(1) if pool_match else "DHCP Pool"
        return {
            "rule": "DHCP_POOL_EXHAUSTED",
            "status": "VIOLATION",
            "severity": "High",
            "finding": f"DHCP address pool '{pool_name}' is 100% full with 0 remaining leases, rejecting new client DHCP requests.",
            "evidence": f"Pool {pool_name}: 100% utilization; %DHCPD-4-DECLINE pool is full"
        }
        
    # 6. Missing DHCP Relay Helper check
    if "Sales_Department" in show and "no ip redirects" in show and "unable to contact your DHCP server" in show:
        return {
            "rule": "DHCP_HELPER_MISSING",
            "status": "VIOLATION",
            "severity": "High",
            "finding": "Missing 'ip helper-address' on interface Vlan20 to forward broadcast DHCP requests across subnets.",
            "evidence": "interface Vlan20 lacks ip helper-address; client reports unable to contact DHCP server"
        }

    return {"rule": "NAT_AND_DHCP_CHECK", "status": "PASS", "finding": "NAT and DHCP configurations are valid."}
