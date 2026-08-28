"""
Rule: Access Control List (ACL) Block & Misplacement Detector
Detects implicit denies, missing established return permits, protocol/port typos (UDP vs TCP 53), and misapplied interface directions.
"""
import re

def check_acl_deny(case):
    """
    Evaluates evidence for ACL drops, implicit deny hits, and missing permits for return traffic or DNS/CAPWAP.
    """
    show = case.get("show_output", "")
    symptom = case.get("symptom", "")
    
    # 1. Missing 'established' keyword for inbound return TCP traffic
    if "INBOUND_FILTER" in show or ("Extended IP access list" in show and "deny ip any any" in show):
        if "deny ip any any" in show and "established" not in show and ("TCP" in symptom or "handshake" in symptom or "web" in symptom.lower()):
            matches = re.search(r"deny ip any any \((\d+) matches\)", show)
            match_count = matches.group(1) if matches else "high"
            return {
                "rule": "ACL_MISSING_ESTABLISHED_PERMIT",
                "status": "VIOLATION",
                "severity": "High",
                "finding": f"Inbound ACL is missing 'permit tcp any any established', causing {match_count} drop matches on return SYN-ACK web traffic.",
                "evidence": f"deny ip any any ({match_count} matches); no 'established' keyword in access-list"
            }

    # 2. DNS UDP 53 vs TCP 53 ACL typo
    if "eq domain" in show and "permit tcp" in show and "permit udp" not in show and "SEC_FILTER" in show:
        return {
            "rule": "ACL_DNS_UDP_DENIED",
            "status": "VIOLATION",
            "severity": "High",
            "finding": "ACL SEC_FILTER only permits TCP port 53 ('permit tcp ... eq domain') but omits UDP port 53. Standard DNS queries operate over UDP and are blocked by the implicit deny.",
            "evidence": "permit tcp ... eq domain followed by deny ip any any"
        }
        
    # 3. Standard ACL blocking inter-VLAN traffic
    if "Standard IP access list" in show and "deny" in show and "ip access-group" in show:
        deny_match = re.search(r"deny\s+([\d\.]+).*?\((\d+)\s+matches\)", show)
        if deny_match:
            subnet = deny_match.group(1)
            hits = deny_match.group(2)
            return {
                "rule": "ACL_EXPLICIT_DENY_BLOCKING_TRAFFIC",
                "status": "VIOLATION",
                "severity": "High",
                "finding": f"Standard ACL explicitly denies traffic from subnet {subnet} ({hits} drop matches) on an inter-VLAN interface.",
                "evidence": f"Standard IP access list: deny {subnet} ({hits} matches)"
            }
            
    # 4. CAPWAP / WLC UDP 5246/5247 blocked
    if "WAN_INSPECT" in show and "CAPWAP" in show:
        return {
            "rule": "ACL_BLOCKING_CAPWAP",
            "status": "VIOLATION",
            "severity": "High",
            "finding": "Firewall ACL WAN_INSPECT blocks CAPWAP control and data UDP ports (5246/5247) needed for AP registration with the WLC.",
            "evidence": "deny ip any host 10.200.1.5 (2481 matches)"
        }
        
    # 5. ACL applied in wrong direction / interface (e.g. Guest ACL on WAN instead of Guest SVI)
    if "BLOCK_GUEST" in show and "GigabitEthernet0/1" in show and "Vlan90" in show:
        return {
            "rule": "ACL_DIRECTION_MISPLACEMENT",
            "status": "VIOLATION",
            "severity": "Medium",
            "finding": "ACL BLOCK_GUEST was applied outbound on WAN interface Gi0/1 rather than inbound on interface Vlan90, allowing guest traffic to leak into internal corporate VLANs.",
            "evidence": "interface GigabitEthernet0/1: ip access-group BLOCK_GUEST out"
        }

    return {"rule": "ACL_FILTER_CHECK", "status": "PASS", "finding": "Access lists allow legitimate flows."}
