"""
Rule: Interface Down & Port Security / BPDU Guard / Duplex Checker
Detects err-disabled ports, BPDU guard violations, port security shutdowns, and duplex mismatch collisions.
"""
import re

def check_interface_down(case):
    """
    Evaluates interface operational status, line protocol, hardware errors, and security shutdown states.
    """
    show = case.get("show_output", "")
    
    # 1. Check for BPDU Guard err-disable
    if "%SPANTREE-2-BLOCK_BPDUGUARD" in show or "bpduguard error detected" in show or ("err-disabled" in show and "bpduguard" in show.lower()):
        intf_match = re.search(r"(Gi\S+|GigabitEthernet\S+|FastEthernet\S+).*?err-disabled", show)
        intf = intf_match.group(1) if intf_match else "interface"
        return {
            "rule": "BPDU_GUARD_ERR_DISABLED",
            "status": "VIOLATION",
            "severity": "High",
            "finding": f"Interface {intf} entered err-disabled state due to BPDU Guard detecting unauthorized BPDUs on a PortFast-enabled edge port.",
            "evidence": "%SPANTREE-2-BLOCK_BPDUGUARD: Disabling port."
        }
        
    # 2. Check for Port Security Violation / Secure-shutdown
    if "Secure-shutdown" in show or ("err-disabled" in show and "port-security" in show.lower()):
        viol_match = re.search(r"Security Violation Count\s*:\s*([1-9]\d*)", show)
        mac_match = re.search(r"Last Source Address:Vlan\s*:\s*([0-9a-fA-F\.:]+)", show)
        viol_count = viol_match.group(1) if viol_match else "1"
        viol_mac = mac_match.group(1) if mac_match else "unauthorized device"
        return {
            "rule": "PORT_SECURITY_VIOLATION",
            "status": "VIOLATION",
            "severity": "High",
            "finding": f"Port Security violation triggered by MAC {viol_mac} (Violation Count: {viol_count}). Port placed in err-disabled shutdown.",
            "evidence": f"Port Status: Secure-shutdown, Last Source Address: {viol_mac}"
        }
        
    # 3. Check for Duplex Mismatch / Late Collisions
    if "late collision" in show and ("Half-duplex" in show or "input errors" in show):
        late_col_match = re.search(r"(\d+)\s+late collision", show)
        crc_match = re.search(r"(\d+)\s+CRC", show)
        late_cols = late_col_match.group(1) if late_col_match else "numerous"
        crc_errs = crc_match.group(1) if crc_match else "numerous"
        return {
            "rule": "DUPLEX_MISMATCH_LATE_COLLISIONS",
            "status": "VIOLATION",
            "severity": "Medium",
            "finding": f"Duplex mismatch detected: Interface is operating in Half-duplex with {late_cols} late collisions and {crc_errs} CRC errors.",
            "evidence": f"Half-duplex, {late_cols} late collision, {crc_errs} CRC errors"
        }
        
    # 4. Check for STP Root Guard Inconsistency
    if "Root Inconsistent" in show or "%SPANTREE-2-ROOTGUARDBLOCK" in show:
        return {
            "rule": "STP_ROOT_GUARD_BLOCK",
            "status": "VIOLATION",
            "severity": "High",
            "finding": "STP Root Guard blocked the downstream port into 'Root Inconsistent' state after receiving superior BPDUs.",
            "evidence": "Inconsistency: Root Inconsistent; %SPANTREE-2-ROOTGUARDBLOCK"
        }

    return {"rule": "INTERFACE_DOWN_CHECK", "status": "PASS", "finding": "Interface is up and operating normally."}
