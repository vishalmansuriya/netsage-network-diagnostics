"""
Rule: Subnet Mask & IP Range Mismatch Detector
Validates host subnet mask, prefix lengths, and broadcast domain boundaries against router interfaces.
"""
import re
import ipaddress

def check_mask_mismatch(case):
    """
    Evaluates evidence for subnet mask discrepancies between hosts and default gateways.
    """
    show = case.get("show_output", "")
    
    # 1. Look for host IP / mask vs router IP / mask
    host_ip_match = re.search(r"IPv4 Address[.\s:]+([\d\.]+)", show)
    host_mask_match = re.search(r"Subnet Mask[.\s:]+([\d\.]+)", show)
    router_int_match = re.search(r"Internet address is\s+([\d\.]+)/(\d+)", show)
    
    if host_ip_match and host_mask_match and router_int_match:
        host_ip = host_ip_match.group(1)
        host_mask = host_mask_match.group(1)
        rtr_ip = router_int_match.group(1)
        rtr_prefix = int(router_int_match.group(2))
        
        try:
            host_net = ipaddress.IPv4Network(f"{host_ip}/{host_mask}", strict=False)
            rtr_net = ipaddress.IPv4Network(f"{rtr_ip}/{rtr_prefix}", strict=False)
            
            if host_net.prefixlen != rtr_net.prefixlen:
                # Check if router IP is outside host's subnet
                rtr_addr = ipaddress.IPv4Address(rtr_ip)
                if rtr_addr not in host_net:
                    return {
                        "rule": "SUBNET_MASK_MISMATCH",
                        "status": "VIOLATION",
                        "severity": "High",
                        "finding": f"Subnet mask mismatch: Host has {host_ip}/{host_mask} (Subnet: {host_net}) while Gateway is {rtr_ip}/{rtr_prefix} (Subnet: {rtr_net}). Gateway is outside host's local subnet.",
                        "evidence": f"Host mask {host_mask} != Router prefix /{rtr_prefix}"
                    }
        except Exception:
            pass

    return {"rule": "MASK_MISMATCH_CHECK", "status": "PASS", "finding": "No subnet mask mismatch detected."}
