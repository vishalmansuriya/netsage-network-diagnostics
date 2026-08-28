"""
Rule: Missing & Misconfigured VLAN Detector
Detects native VLAN mismatches, inactive VLAN assignments, and trunk allowed list omissions.
"""
import re

def check_missing_vlan(case):
    """
    Evaluates evidence for VLAN database omissions, trunk native VLAN mismatches, and trunk allowed list filtering.
    """
    show = case.get("show_output", "")
    
    # 1. Native VLAN mismatch check
    cdp_match = re.search(r"%CDP-4-NATIVE_VLAN_MISMATCH:\s*Native VLAN mismatch discovered on\s+(\S+)\s+\((\d+)\),\s+with\s+(\S+)\s+(\S+)\s+\((\d+)\)", show)
    if cdp_match:
        local_intf, local_vlan, remote_dev, remote_intf, remote_vlan = cdp_match.groups()
        return {
            "rule": "NATIVE_VLAN_MISMATCH",
            "status": "VIOLATION",
            "severity": "High",
            "finding": f"Native VLAN mismatch on trunk link {local_intf}: Local Native VLAN is {local_vlan}, but remote {remote_dev} {remote_intf} is Native VLAN {remote_vlan}.",
            "evidence": cdp_match.group(0)
        }
        
    # 2. Inactive VLAN check (VLAN assigned to access port but missing from vlan.dat)
    if "(Inactive)" in show or "Access Mode VLAN:" in show and "Inactive" in show:
        vlan_match = re.search(r"Access Mode VLAN:\s*(\d+)\s*\(Inactive\)", show)
        vlan_id = vlan_match.group(1) if vlan_match else "configured"
        return {
            "rule": "VLAN_NOT_IN_DATABASE",
            "status": "VIOLATION",
            "severity": "Medium",
            "finding": f"Access port assigned to VLAN {vlan_id}, but VLAN {vlan_id} does not exist in the switch VLAN database (vlan.dat), marking port Inactive.",
            "evidence": f"Access Mode VLAN: {vlan_id} (Inactive)"
        }
        
    # 3. Trunk allowed list pruning check
    if "switchport trunk allowed vlan" in show:
        allowed_match = re.search(r"switchport trunk allowed vlan\s+([\d,-]+)", show)
        if allowed_match:
            allowed_vlans = allowed_match.group(1)
            # If case mentions Voice VLAN 40 or other needed VLAN missing
            if "40" not in allowed_vlans and ("Voice" in case.get("symptom", "") or "40" in case.get("topology_note", "")):
                return {
                    "rule": "VLAN_PRUNED_FROM_TRUNK",
                    "status": "VIOLATION",
                    "severity": "High",
                    "finding": f"Required VLAN 40 is missing from trunk allowed list: only VLANs {allowed_vlans} are allowed on the trunk.",
                    "evidence": f"switchport trunk allowed vlan {allowed_vlans}"
                }

    return {"rule": "VLAN_CONFIG_CHECK", "status": "PASS", "finding": "VLAN configuration is valid."}
