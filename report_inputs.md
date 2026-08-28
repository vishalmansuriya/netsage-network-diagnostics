# NetSage AI report inputs

## 1. Dataset framing check

Required wording in the repository:

> 32 synthetically generated, internally consistent cases, validated for topology/IP/VLAN coherence.

`README.md` and `demo/demo_script.md` use this wording. A repository-wide exact-term check was run across all tracked content.

Result: 0 matches. No legacy provenance claim of that type remains in the repository.

`scripts/build_data.py` is the data source for `data/cases.csv` and the 32 files under `data/raw_evidence/`; each evidence file is labelled `NETSAGE AI - SYNTHETIC CLI EVIDENCE`.

## 2. Metrics and re-execution review

### Recorded review-log metrics

Source files read directly:

- `review/review_log.csv`
- `dashboard/metrics.json`

`review/review_log.csv` contains 32 data rows.

| Metric | Row count | Formula | Recomputed value | Value in `dashboard/metrics.json` |
|---|---:|---|---:|---:|
| Accepted | 32 | `32 / 32 * 100` | 100.0% | 100.0% |
| Edited | 0 | `0 / 32 * 100` | 0.0% | 0.0% |
| Rejected | 0 | `0 / 32 * 100` | 0.0% | 0.0% |
| Rule-hit (`FLAGGED`) | 29 | `29 / 32 * 100` | 90.6% | 90.6% |

The verdict counts reconcile: `32 + 0 + 0 = 32`. The non-hit rule count is 3 `CLEAN` rows: `3 / 32 * 100 = 9.4%`.

### Pipeline execution and review provenance

Command executed:

```powershell
python pipeline/run_diagnosis.py --live
```

Execution result: 32 response JSON files were written to `pipeline/responses/`; all 32 passed the schema check. Each output has `"engine_mode": "simulation"`.

This is not a real hosted-model run. `pipeline/ai_client.py` has no implemented API dispatch in its `live` branch: it returns `MOCK_RESPONSES`. The environment contained no `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`. Therefore the existing review log and the re-execution below must not be described as a human audit of real-model outputs.

### Re-execution review of the 32 emitted JSON records

Method: for each response written by the executed pipeline, the emitted `root_cause` was compared with the corresponding `expected_fault` in `data/cases.csv`. A response was marked `Accepted` when it identified the same underlying fault. No response required a diagnosis correction or named a different root cause.

| Case | Expected fault | Emitted JSON `root_cause` | Re-execution verdict |
|---|---|---|---|
| CASE-001 | Native VLAN mismatch: Dist-SW1 VLAN 10 vs Dist-SW2 VLAN 20 on Gi0/1. | 802.1Q trunk native-VLAN mismatch between Dist-SW1 VLAN 10 and Dist-SW2 VLAN 20 on Gi0/1. | Accepted |
| CASE-002 | Gi0/5 is in VLAN 50, which is absent from the switch VLAN database. | Gi0/5 is assigned to absent VLAN 50 and is Inactive. | Accepted |
| CASE-003 | Voice VLAN 40 is pruned from Gi0/24's allowed trunk VLAN list. | VLAN 40 is pruned from the Gi0/24 uplink trunk list. | Accepted |
| CASE-004 | BPDU Guard put Gi0/12 in err-disabled after it received BPDUs. | BPDU Guard put Gi0/12 in err-disabled after unexpected BPDUs on a PortFast edge port. | Accepted |
| CASE-005 | SRV-01 has a /28 mask, making 192.168.10.1 appear off-subnet. | SRV-01 has a /28 mask mismatch that isolates it from 192.168.10.1. | Accepted |
| CASE-006 | DB-01 uses 10.10.30.1 instead of local gateway 10.10.20.1. | DB-01 uses VLAN 30 SVI 10.10.30.1 instead of VLAN 20 SVI 10.10.20.1. | Accepted |
| CASE-007 | OSPF MTU mismatch: 1500 on Core-R1 vs 1400 on Dist-R2. | OSPF MTU mismatch: 1500 on Core-R1 vs 1400 on Dist-R2. | Accepted |
| CASE-008 | No default route to ISP gateway 203.0.113.1. | Missing default static route to 203.0.113.1. | Accepted |
| CASE-009 | Gi0/2 is configured as an OSPF passive interface. | Gi0/2 is configured as an OSPF passive interface. | Accepted |
| CASE-010 | BGP `remote-as` 65510 does not match ISP AS 65500. | BGP `remote-as` 65510 does not match ISP AS 65500. | Accepted |
| CASE-011 | Static-route next hop 10.254.1.1 is unreachable, causing recursive lookup failure. | Next hop 10.254.1.1 is unreachable, causing recursive lookup failure. | Accepted |
| CASE-012 | NAT inside/outside roles are inverted on LAN Gi0/0 and WAN Gi0/1. | NAT inside/outside roles are inverted on LAN Gi0/0 and WAN Gi0/1. | Accepted |
| CASE-013 | NAT ACL 10 permits 192.168.10.0/24 instead of 192.168.20.0/24. | NAT ACL 10 permits 192.168.10.0/24 instead of 192.168.20.0/24. | Accepted |
| CASE-014 | NAT pool includes ISP gateway 198.51.100.1. | NAT pool range includes ISP gateway 198.51.100.1. | Accepted |
| CASE-015 | Static NAT maps the server to .250 instead of DNS IP .205. | Static NAT maps 192.168.100.10 to .250 instead of .205. | Accepted |
| CASE-016 | Vlan20 lacks `ip helper-address 10.1.1.50`. | Vlan20 lacks `ip helper-address 10.1.1.50`. | Accepted |
| CASE-017 | DHCP pool GUEST_WIFI is exhausted at 51/51 leases. | DHCP pool GUEST_WIFI is 100% full at 51/51 leases. | Accepted |
| CASE-018 | Rogue DHCP server on Gi0/8 is active because DHCP Snooping is disabled. | Rogue DHCP server on Gi0/8 distributes unauthorized 192.168.88.0/24 leases because Snooping is disabled. | Accepted |
| CASE-019 | DHCP leased static printer IP 192.168.1.25 to a dynamic host. | DHCP leased static printer IP 192.168.1.25 to a PC. | Accepted |
| CASE-020 | DHCP leased unexcluded gateway IP 10.50.0.254. | DHCP leased gateway IP 10.50.0.254 because exclusions stop at .50. | Accepted |
| CASE-021 | Outbound standard ACL 10 on Gi0/3 denies 192.168.10.0/24. | Outbound standard ACL 10 on Gi0/3 denies 192.168.10.0/24. | Accepted |
| CASE-022 | WAN inbound ACL lacks `permit tcp any any established`. | WAN inbound ACL lacks `permit tcp any any established`. | Accepted |
| CASE-023 | ACL permits TCP/53 but omits UDP/53. | ACL permits TCP/53 but omits UDP/53. | Accepted |
| CASE-024 | Guest ACL is on WAN egress, not Vlan90 ingress. | Guest ACL is on WAN egress, not Vlan90 ingress. | Accepted |
| CASE-025 | DHCP pool uses retired DNS 10.10.1.20 instead of 10.10.1.50. | DHCP pool uses retired DNS 10.10.1.20 instead of 10.10.1.50. | Accepted |
| CASE-026 | Public resolvers are used without an internal `.corp.local` forwarder. | Public resolvers are used without an internal `.corp.local` forwarder. | Accepted |
| CASE-027 | Tunnel MTU plus suppressed ICMP fragmentation responses creates a PMTU black hole. | Tunnel MTU plus `no ip unreachables` creates a PMTU black hole. | Accepted |
| CASE-028 | Hardcoded full duplex vs auto-negotiated half duplex causes errors. | Hardcoded full duplex vs auto-negotiated half duplex causes late collisions. | Accepted |
| CASE-029 | Port-security maximum of one MAC was exceeded. | Port-security maximum of one MAC was exceeded. | Accepted |
| CASE-030 | Rogue host poisoned gateway ARP entries while DAI is disabled. | Rogue host poisoned gateway ARP entries while DAI is disabled. | Accepted |
| CASE-031 | Root Guard placed Gi0/24 into Root Inconsistent after superior BPDUs. | Root Guard placed Gi0/24 into Root Inconsistent after superior BPDUs. | Accepted |
| CASE-032 | Firewall ACL blocks CAPWAP UDP 5246/5247 between LAPs and WLC. | Firewall ACL blocks CAPWAP UDP 5246/5247 for LAP discovery. | Accepted |

Re-execution counts: Accepted `32 / 32 = 100.0%`; Edited `0 / 32 = 0.0%`; Rejected `0 / 32 = 0.0%`; rule-hit `29 / 32 = 90.6%`.

These re-execution figures measure agreement of the embedded simulation response map with the embedded expected-fault labels. They are not a live-model evaluation and should not replace a genuine, independently recorded human review.

## 3. Requested case write-ups from the executed pipeline

All six JSON records below were written by the command in the execution record. Their `engine_mode` is `simulation`.

### CASE-007

Actual pipeline JSON:

```json
{
  "case_id": "CASE-007",
  "root_cause": "OSPF interface MTU mismatch on transit link Gi0/0 (Core-R1 MTU 1500 vs Dist-R2 MTU 1400) halting neighbor adjacency in EXSTART/DBD state.",
  "osi_layer": 3,
  "confidence": "high",
  "evidence": "Core-R1 Gi0/0 'MTU is 1500 bytes', Dist-R2 Gi0/0 'MTU is 1400 bytes'; 'show ip ospf neighbor' shows State: EXSTART/  -.",
  "next_command": "show ip ospf neighbor GigabitEthernet0/0",
  "fix_steps": ["configure terminal", "interface GigabitEthernet0/0", "ip mtu 1500", "end", "clear ip ospf process"],
  "reasoning_summary": "During the OSPF EXSTART state, routers negotiate master/slave and exchange DBD packets. If MTU does not match, the larger DBD packet is dropped, preventing transition to FULL.",
  "diagnosed_at": "2026-08-28T15:26:07Z",
  "engine_mode": "simulation",
  "schema_valid": true,
  "rule_checker_verdict": "FLAGGED",
  "rule_checker_violation": "OSPF MTU mismatch between neighbors: Local MTU is 1500 bytes vs Remote MTU 1400 bytes, causing EXSTART/DBD state hang."
}
```

Correct diagnosis: OSPF MTU mismatch on Gi0/0 (1500 vs 1400) causes the EXSTART/DBD failure. Divergence classification: not applicable; the emitted root cause matches the expected fault.

### CASE-012

Actual pipeline JSON:

```json
{
  "case_id": "CASE-012",
  "root_cause": "NAT inside and outside interface directions are inverted (LAN Gi0/0 has 'ip nat outside' and WAN Gi0/1 has 'ip nat inside').",
  "osi_layer": 3,
  "confidence": "high",
  "evidence": "interface Gi0/0 (LAN): 'ip nat outside', interface Gi0/1 (WAN): 'ip nat inside'; 'show ip nat translations' is completely empty.",
  "next_command": "show ip nat statistics",
  "fix_steps": ["configure terminal", "interface GigabitEthernet0/0", "no ip nat outside", "ip nat inside", "interface GigabitEthernet0/1", "no ip nat inside", "ip nat outside", "end", "clear ip nat translation *"],
  "reasoning_summary": "NAT engines translate source addresses from inside-to-outside interfaces. Inverting the tags causes outbound client traffic to be ignored by the translation engine.",
  "diagnosed_at": "2026-08-28T15:26:07Z",
  "engine_mode": "simulation",
  "schema_valid": true,
  "rule_checker_verdict": "FLAGGED",
  "rule_checker_violation": "NAT interface direction is inverted: LAN interface is marked as 'ip nat outside' and WAN interface as 'ip nat inside', preventing translations."
}
```

Correct diagnosis: NAT inside/outside direction is inverted on Gi0/0 and Gi0/1. Divergence classification: not applicable; the emitted root cause matches the expected fault.

### CASE-018

Actual pipeline JSON:

```json
{
  "case_id": "CASE-018",
  "root_cause": "Rogue DHCP server connected to switch port Gi0/8 distributing unauthorized IP leases (192.168.88.0/24) because DHCP Snooping is disabled.",
  "osi_layer": 7,
  "confidence": "high",
  "evidence": "Client ipconfig shows Default Gateway 192.168.88.1 and DHCP Server 192.168.88.1; 'show ip dhcp snooping' shows Switch DHCP snooping is disabled.",
  "next_command": "show mac address-table dynamic interface Gi0/8",
  "fix_steps": ["configure terminal", "ip dhcp snooping", "ip dhcp snooping vlan 10", "interface GigabitEthernet0/8", "shutdown", "end"],
  "reasoning_summary": "Unmanaged Wi-Fi router answered DHCP discoveries faster than the corporate server. Enabling DHCP snooping treats edge ports as untrusted.",
  "diagnosed_at": "2026-08-28T15:26:07Z",
  "engine_mode": "simulation",
  "schema_valid": true,
  "rule_checker_verdict": "CLEAN",
  "rule_checker_violation": "All deterministic rules passed."
}
```

Correct diagnosis: a rogue DHCP server on Gi0/8 distributes 192.168.88.0/24 leases because DHCP Snooping is disabled. Divergence classification: not applicable; the emitted root cause matches the expected fault.

### CASE-026

Actual pipeline JSON:

```json
{
  "case_id": "CASE-026",
  "root_cause": "Split-brain DNS misconfiguration: Branch-GW name-servers are configured with public resolvers (8.8.8.8) with no conditional forwarder for internal zone 'corp.local'.",
  "osi_layer": 7,
  "confidence": "medium",
  "evidence": "show run: 'ip name-server 8.8.8.8' and 'show hosts' shows 'Default domain is corp.local'; internal DNS server 10.0.0.5 is not referenced.",
  "next_command": "show hosts",
  "fix_steps": ["configure terminal", "ip name-server 10.0.0.5 8.8.8.8", "end", "write memory"],
  "reasoning_summary": "Public recursive resolvers cannot resolve non-public corporate TLDs (.corp.local), requiring internal name servers to be queried first.",
  "diagnosed_at": "2026-08-28T15:26:07Z",
  "engine_mode": "simulation",
  "schema_valid": true,
  "rule_checker_verdict": "CLEAN",
  "rule_checker_violation": "All deterministic rules passed."
}
```

Correct diagnosis: Branch-GW needs an internal resolver/forwarder for `corp.local`, not only public resolvers. Divergence classification: not applicable; the emitted root cause matches the expected fault.

### CASE-015

Actual pipeline JSON:

```json
{
  "case_id": "CASE-015",
  "root_cause": "Static 1-to-1 NAT configuration typo: mapped inside server 192.168.100.10 to 203.0.113.250 instead of registered public DNS IP 203.0.113.205.",
  "osi_layer": 3,
  "confidence": "medium",
  "evidence": "show run contains 'ip nat inside source static 192.168.100.10 203.0.113.250' while DNS query returns 203.0.113.205.",
  "next_command": "show ip nat translations",
  "fix_steps": ["configure terminal", "no ip nat inside source static 192.168.100.10 203.0.113.250", "ip nat inside source static 192.168.100.10 203.0.113.205", "end", "write memory"],
  "reasoning_summary": "Digit transposition in the static NAT statement caused traffic destined for public DNS IP 203.0.113.205 to fail to translate to the private server.",
  "diagnosed_at": "2026-08-28T15:26:07Z",
  "engine_mode": "simulation",
  "schema_valid": true,
  "rule_checker_verdict": "FLAGGED",
  "rule_checker_violation": "Static NAT outside IP (203.0.113.250) does not match public DNS A-record (203.0.113.205) due to digit transposition."
}
```

Correct diagnosis: the static NAT mapping has `.250` where the public DNS address is `.205`. Divergence classification: not applicable; the emitted root cause matches the expected fault.

### CASE-020

Actual pipeline JSON:

```json
{
  "case_id": "CASE-020",
  "root_cause": "DHCP server leased default gateway IP 10.50.0.254 to a client because 'ip dhcp excluded-address' only covered .1 to .50.",
  "osi_layer": 7,
  "confidence": "medium",
  "evidence": "show run: 'default-router 10.50.0.254' while excluded range is '10.50.0.1 10.50.0.50'; 'show ip dhcp binding' shows 10.50.0.254 leased.",
  "next_command": "show ip dhcp binding 10.50.0.254",
  "fix_steps": ["configure terminal", "ip dhcp excluded-address 10.50.0.254", "end", "clear ip dhcp binding 10.50.0.254"],
  "reasoning_summary": "Any static IP in a subnet must be explicitly excluded from dynamic DHCP pools to prevent address hijacking.",
  "diagnosed_at": "2026-08-28T15:26:07Z",
  "engine_mode": "simulation",
  "schema_valid": true,
  "rule_checker_verdict": "FLAGGED",
  "rule_checker_violation": "Default gateway IP 10.50.0.254 is leased by DHCP server to a dynamic client because it was not excluded."
}
```

Correct diagnosis: the DHCP exclusion range omitted the gateway IP 10.50.0.254, so DHCP leased it. Divergence classification: not applicable; the emitted root cause matches the expected fault.

## 4. Case-diversity check

The `expected_fault` entries in `data/cases.csv` were inspected within each `concept_tag` for cases with the same underlying fault differing only by IP address, hostname, or interface name. No near-duplicate cases were found.

| Concept tag | Cases reviewed | Result |
|---|---|---|
| VLAN | CASE-001 to CASE-003 | Native VLAN mismatch, missing VLAN, and trunk pruning are distinct faults. |
| Routing | CASE-005 to CASE-011 | Mask, gateway, OSPF MTU, default route, passive interface, BGP AS, and recursive-next-hop failures are distinct. |
| NAT | CASE-012 to CASE-015 | Interface direction, ACL subnet, pool overlap, and static-mapping typo are distinct. |
| DHCP | CASE-016 to CASE-020 | Missing relay, pool exhaustion, rogue server, duplicate lease, and gateway lease are distinct. |
| ACL | CASE-021 to CASE-024 | Explicit deny, missing established rule, UDP DNS omission, and wrong attachment point are distinct. |
| DNS | CASE-025 to CASE-027 | Stale DHCP DNS option, internal-zone forwarding, and VPN PMTU failure are distinct. |
| Wireless/L2 | CASE-004 and CASE-028 to CASE-032 | BPDU Guard, duplex, port security, ARP poisoning, Root Guard, and CAPWAP filtering are distinct. |

## Team contribution split

_To be completed by the project team._
