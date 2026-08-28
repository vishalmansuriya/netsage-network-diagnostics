"""
Rule: Default Gateway Mismatch Detector
Validates whether configured default gateway resides on the host's local subnet or is mispointed to another VLAN.
"""
import re
import ipaddress

def check_gateway_mismatch(case):
    """
    Evaluates evidence for default gateways configured in the wrong subnet or pointing to an unrouted VLAN.
    """
    show = case.get("show_output", "")
    
    # Check Linux / Windows host default route vs interface IP
    host_ip_match = re.search(r"inet\s+([\d\.]+)\s+netmask\s+([\d\.]+)", show)
    def_gw_match = re.search(r"default via\s+([\d\.]+)", show)
    
    if host_ip_match and def_gw_match:
        host_ip = host_ip_match.group(1)
        netmask = host_ip_match.group(2)
        gw_ip = def_gw_match.group(1)
        
        try:
            local_net = ipaddress.IPv4Network(f"{host_ip}/{netmask}", strict=False)
            gw_addr = ipaddress.IPv4Address(gw_ip)
            
            if gw_addr not in local_net:
                return {
                    "rule": "DEFAULT_GATEWAY_MISMATCH",
                    "status": "VIOLATION",
                    "severity": "High",
                    "finding": f"Default gateway {gw_ip} is not in host's local subnet {local_net} (Host IP: {host_ip}). Host cannot reach its gateway directly.",
                    "evidence": f"inet {host_ip} netmask {netmask} vs default via {gw_ip}"
                }
        except Exception:
            pass
            
    # Check for decommissioned DNS / Gateway server ping failure
    if "Success rate is 0 percent" in show and "dns-server" in show:
        ping_ip = re.search(r"Sending 5, 100-byte ICMP Echos to ([\d\.]+).*?Success rate is 0 percent", show, re.DOTALL)
        if ping_ip:
            target = ping_ip.group(1)
            return {
                "rule": "UNREACHABLE_INFRASTRUCTURE_SERVER",
                "status": "VIOLATION",
                "severity": "High",
                "finding": f"Configured DNS / Gateway server {target} is completely unreachable (0% ping success rate).",
                "evidence": f"Ping to {target} failed: Success rate is 0 percent"
            }

    return {"rule": "GATEWAY_MISMATCH_CHECK", "status": "PASS", "finding": "Default gateway configuration is valid."}
