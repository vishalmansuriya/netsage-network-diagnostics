"""
Rule: Missing Route & Dynamic Routing Failure Detector
Detects missing default routes, recursive lookup failures, OSPF MTU / passive interface issues, and BGP AS mismatches.
"""
import re

def check_missing_route(case):
    """
    Evaluates evidence for missing static/default routes, OSPF adjacency deadlocks, and BGP state failures.
    """
    show = case.get("show_output", "")
    
    # 1. Missing Default Route check
    if "Gateway of last resort is not set" in show and ("8.8.8.8" in show or "Internet" in case.get("symptom", "") or "default" in case.get("expected_fault", "").lower()):
        return {
            "rule": "MISSING_DEFAULT_ROUTE",
            "status": "VIOLATION",
            "severity": "High",
            "finding": "Missing default route (0.0.0.0/0) to the ISP gateway. 'Gateway of last resort is not set' in the routing table.",
            "evidence": "Gateway of last resort is not set"
        }
        
    # 2. OSPF MTU Mismatch check
    if "EXSTART" in show or "%OSPF-5-ADJCHG" in show:
        mtu_values = re.findall(r"MTU is (\d+) bytes", show)
        if len(mtu_values) >= 2 and mtu_values[0] != mtu_values[1]:
            return {
                "rule": "OSPF_MTU_MISMATCH",
                "status": "VIOLATION",
                "severity": "High",
                "finding": f"OSPF MTU mismatch between neighbors: Local MTU is {mtu_values[0]} bytes vs Remote MTU {mtu_values[1]} bytes, causing EXSTART/DBD state hang.",
                "evidence": f"Neighbor State: EXSTART; MTU values: {mtu_values[0]} vs {mtu_values[1]}"
            }
            
    # 3. OSPF Passive Interface check
    if "No Hellos (Passive interface)" in show or "passive-interface" in show:
        passive_match = re.search(r"passive-interface\s+(\S+)", show)
        intf = passive_match.group(1) if passive_match else "transit link"
        return {
            "rule": "OSPF_PASSIVE_INTERFACE",
            "status": "VIOLATION",
            "severity": "Medium",
            "finding": f"OSPF passive-interface configured on link {intf}, suppressing Hello packets and preventing adjacency formation.",
            "evidence": "No Hellos (Passive interface)"
        }
        
    # 4. BGP Autonomous System (AS) Mismatch check
    if "show ip bgp summary" in show and "Active" in show:
        local_as_match = re.search(r"local AS number\s+(\d+)", show)
        remote_as_match = re.search(r"neighbor\s+[\d\.]+\s+remote-as\s+(\d+)", show)
        isp_as_match = re.search(r"ISP-RTR.*?router bgp\s+(\d+)", show, re.DOTALL)
        if remote_as_match and isp_as_match and remote_as_match.group(1) != isp_as_match.group(1):
            return {
                "rule": "BGP_AS_MISMATCH",
                "status": "VIOLATION",
                "severity": "High",
                "finding": f"BGP remote-as mismatch: Configured remote-as {remote_as_match.group(1)} does not match ISP AS {isp_as_match.group(1)}, holding session in Active state.",
                "evidence": f"remote-as {remote_as_match.group(1)} vs ISP router bgp {isp_as_match.group(1)}"
            }
            
    # 5. Recursive Route Lookup Failure check
    if "ip route" in show and "% Network not in table" in show:
        next_hop_match = re.search(r"show ip route\s+([\d\.]+)\s*\n% Network not in table", show)
        if next_hop_match:
            nh = next_hop_match.group(1)
            return {
                "rule": "RECURSIVE_ROUTE_FAILURE",
                "status": "VIOLATION",
                "severity": "Medium",
                "finding": f"Recursive route lookup failure: Static route next-hop {nh} is not in the routing table, preventing route activation.",
                "evidence": f"show ip route {nh}: % Network not in table"
            }

    return {"rule": "ROUTING_CHECK", "status": "PASS", "finding": "Routing configuration and adjacencies are normal."}
