# NetSage AI — Pipeline Re-execution Evidence Log

## Scope and limitation

On 2026-08-28, `python pipeline/run_diagnosis.py --live` was executed for the full 32-case dataset. The command wrote 32 schema-valid response files. Each response reports `"engine_mode": "simulation"`: `pipeline/ai_client.py` currently returns its embedded `MOCK_RESPONSES` map and has no live-provider dispatch implementation. This is therefore a comparison of executed simulation outputs with the expected-fault labels, not a hosted-model evaluation or a human-review study.

The six records below replace the prior hypothetical failure narratives. For each, the emitted `root_cause` matches `data/cases.csv`; no prompt gap, model limitation, or ambiguity was observed in this execution.

## CASE-007 — OSPF MTU mismatch

### Actual pipeline JSON

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

Correct diagnosis from `data/cases.csv`: OSPF MTU mismatch on Gi0/0 (Core-R1 1500, Dist-R2 1400), causing the EXSTART/DBD failure. Divergence classification: none; the emitted diagnosis matches the expected fault.

## CASE-012 — NAT inside/outside inversion

### Actual pipeline JSON

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

Correct diagnosis from `data/cases.csv`: LAN Gi0/0 is incorrectly marked `ip nat outside` and WAN Gi0/1 `ip nat inside`. Divergence classification: none; the emitted diagnosis matches the expected fault.

## CASE-018 — Rogue DHCP server

### Actual pipeline JSON

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

Correct diagnosis from `data/cases.csv`: a rogue DHCP server on Gi0/8 distributes 192.168.88.0/24 leases because DHCP Snooping is disabled. Divergence classification: none; the emitted diagnosis matches the expected fault.

## CASE-026 — Internal DNS forwarding

### Actual pipeline JSON

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

Correct diagnosis from `data/cases.csv`: Branch-GW uses public resolvers with no internal `corp.local` forwarder to 10.0.0.5. Divergence classification: none; the emitted diagnosis matches the expected fault.

## CASE-015 — Static NAT public-IP typo

### Actual pipeline JSON

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

Correct diagnosis from `data/cases.csv`: the static mapping uses 203.0.113.250 instead of registered public DNS address 203.0.113.205. Divergence classification: none; the emitted diagnosis matches the expected fault.

## CASE-020 — DHCP gateway-address lease

### Actual pipeline JSON

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

Correct diagnosis from `data/cases.csv`: 10.50.0.254 was not excluded from DHCP, so it was leased to a client. Divergence classification: none; the emitted diagnosis matches the expected fault.
