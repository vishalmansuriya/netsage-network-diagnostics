# NetSage AI — Dataset Schema Specification

This document defines the schema, constraints, OSI layer classifications, concept tags, and formatting rules for the `cases.csv` dataset and associated raw evidence in the NetSage AI project.

---

## 1. `cases.csv` Column Specifications

| Column Name | Data Type | Required | Allowed Values / Pattern | Description |
|---|---|---|---|---|
| `case_id` | String | Yes | `CASE-001` to `CASE-999` | Unique identifier for each network troubleshooting incident. |
| `symptom` | String | Yes | Plain text summary (10–300 chars) | User-reported or monitoring-alerted symptom (e.g. "Workstations in Sales VLAN cannot obtain IP address"). |
| `topology_note` | String | Yes | Text describing topology context | Architectural layout, device roles, subnets, interfaces, and expected traffic paths. |
| `show_output` | String | Yes | Text snippet or evidence file link | Cisco IOS CLI output capturing the fault state (`show ip route`, `show ip int brief`, etc.). |
| `expected_fault` | String | Yes | Exact technical root cause | Ground truth diagnosis verified by network engineers. |
| `osi_layer` | Integer | Yes | `1` to `7` | Primary OSI reference model layer where the fault originates. |
| `concept_tag` | Enum String | Yes | `VLAN`, `Routing`, `NAT`, `DHCP`, `ACL`, `DNS`, `Wireless/L2` | Core networking domain of the incident. |
| `evidence_file` | String | Yes | `data/raw_evidence/case_XXX_show_output.txt` | Relative file path to the formatted Cisco IOS CLI evidence capture file. |

---

## 2. Taxonomy & Allowed Values

### 2.1 OSI Layer Mapping
- **Layer 1 (Physical):** Cable faults, SFP mismatch, duplex/speed mismatch causing late collisions.
- **Layer 2 (Data Link):** VLAN tagging, 802.1Q trunking, Spanning Tree (STP/RSTP/Root Guard), Port Security, ARP, MAC table errors.
- **Layer 3 (Network):** IP addressing, subnet masking, default gateway misconfiguration, Static routing, OSPF, EIGRP, BGP, NAT/PAT.
- **Layer 4 (Transport):** TCP/UDP port ACL filters, TCP MSS/MTU clipping, TCP connection reset/established flags.
- **Layer 7 (Application):** DHCP server pools & relay helpers, DNS forwarders and resolver timeouts, HTTP proxy blocking.

### 2.2 Concept Tags & Distribution Target
The dataset maintains balanced coverage across 7 technical domains:
- **`VLAN`** ($\approx 12.5\%$): Trunk native VLAN mismatch, missing VLAN database entries, trunk allowed list pruning.
- **`Routing`** ($\approx 22\%$): OSPF MTU mismatch, missing default routes, passive interfaces, BGP AS mismatch, metric blackholes.
- **`NAT`** ($\approx 12.5\%$): Inverted inside/outside interfaces, overload ACL subnet errors, IP pool exhaustion.
- **`DHCP`** ($\approx 15.5\%$): Helper-address omission, pool exhaustion, duplicate static IP conflicts, rogue DHCP servers.
- **`ACL`** ($\approx 12.5\%$): Implicit deny traps, standard ACL applied in wrong direction, missing return traffic permit.
- **`DNS`** ($\approx 9.5\%$): Stale primary server IP, split-brain domain forwarding, path MTU fragmentation drops.
- **`Wireless/L2`** ($\approx 15.5\%$): STP Root Guard inconsistencies, ARP cache poisoning, switchport duplex mismatch, port security err-disable.

---

## 3. Raw Evidence Directory Structure (`data/raw_evidence/`)

For every case in `cases.csv`, a corresponding text file exists in `data/raw_evidence/`:
```
data/raw_evidence/case_001_show_output.txt
data/raw_evidence/case_002_show_output.txt
...
data/raw_evidence/case_032_show_output.txt
```

Each evidence file includes:
1. **Device Header:** Hostname and device role (`Core-SW1#`, `Edge-RTR#`, `Dist-SW2#`).
2. **Executed Show Commands:** Real Cisco IOS show commands (e.g. `show interfaces trunk`, `show ip ospf neighbor`, `show access-lists`).
3. **Internal Consistency Guarantee:** IP addresses, subnet masks, interface IDs (`GigabitEthernet0/1`), VLAN IDs, and MAC addresses match across the topology description and the show output.
