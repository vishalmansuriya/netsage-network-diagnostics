# NetSage AI — Multi-Domain Few-Shot Worked Examples

These few-shot examples demonstrate high-precision network diagnosis across distinct OSI layers and networking domains.

---

### Example 1: Layer 2 Trunking / VLAN Mismatch

**Input:**
```text
Case ID: CASE-EX01
Symptom: CDP error logs flooding console and broadcast traffic leaking between switch SW1 and SW2.
Topology Context: Switch SW1 (Gi0/1) connects to Switch SW2 (Gi0/1) over 802.1Q trunk.

Raw Cisco IOS Show Output:
SW1# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      10

SW1# show log | include %CDP-4-NATIVE_VLAN_MISMATCH
%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (10), with SW2 GigabitEthernet0/1 (20).
```

**Expected AI Response:**
```json
{
  "case_id": "CASE-EX01",
  "root_cause": "Native VLAN mismatch on 802.1Q trunk link Gi0/1 (SW1 configured with Native VLAN 10 while SW2 is on Native VLAN 20).",
  "osi_layer": 2,
  "confidence": "high",
  "evidence": "SW1# show log: '%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (10), with SW2 GigabitEthernet0/1 (20)' and 'show interfaces trunk' indicates Native vlan 10.",
  "next_command": "show interfaces GigabitEthernet0/1 trunk",
  "fix_steps": [
    "configure terminal",
    "interface GigabitEthernet0/1",
    "switchport trunk native vlan 20",
    "end",
    "write memory"
  ],
  "reasoning_summary": "CDP syslog explicitly reports mismatch between local Native VLAN 10 and remote Native VLAN 20. Aligning Native VLAN on both ends eliminates cross-VLAN broadcast leakage."
}
```

---

### Example 2: Layer 3 OSPF Routing / MTU Mismatch

**Input:**
```text
Case ID: CASE-EX02
Symptom: OSPF neighbor state stuck in EXSTART/DBD exchange between Router R1 and R2 across transit link.
Topology Context: R1 (Gi0/0, 10.0.0.1/30) connects to R2 (Gi0/0, 10.0.0.2/30) in OSPF Area 0.

Raw Cisco IOS Show Output:
R1# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
192.168.2.2       1   EXSTART/  -     00:00:33    10.0.0.2        GigabitEthernet0/0

R1# show ip interface GigabitEthernet0/0 | include MTU
  MTU is 1500 bytes

R2# show ip interface GigabitEthernet0/0 | include MTU
  MTU is 1400 bytes
```

**Expected AI Response:**
```json
{
  "case_id": "CASE-EX02",
  "root_cause": "OSPF interface MTU mismatch between R1 (MTU 1500) and R2 (MTU 1400) on link Gi0/0 preventing Database Description (DBD) packet negotiation.",
  "osi_layer": 3,
  "confidence": "high",
  "evidence": "R1 show ip interface Gi0/0 shows 'MTU is 1500 bytes' while R2 shows 'MTU is 1400 bytes'; neighbor state is stuck in 'EXSTART/  -'.",
  "next_command": "show ip ospf neighbor GigabitEthernet0/0",
  "fix_steps": [
    "configure terminal",
    "interface GigabitEthernet0/0",
    "ip mtu 1500",
    "end",
    "clear ip ospf process"
  ],
  "reasoning_summary": "OSPF requires matching MTUs on point-to-point and broadcast links. Because R1 MTU exceeds R2, DBD packets are rejected, halting adjacency in EXSTART."
}
```

---

### Example 3: Layer 7 / Layer 3 DHCP Relay Helper Missing

**Input:**
```text
Case ID: CASE-EX03
Symptom: DHCP clients on VLAN 20 cannot acquire IP addresses and timeout with APIPA addresses.
Topology Context: Core switch SVI interface Vlan20 connects to 192.168.20.0/24. DHCP server resides at 10.1.1.50 in VLAN 10.

Raw Cisco IOS Show Output:
Core-SW# show run interface Vlan20
interface Vlan20
 description Sales_Department
 ip address 192.168.20.1 255.255.255.0
 no ip redirects

Core-SW# show run interface Vlan10
interface Vlan10
 description Server_VLAN
 ip address 10.1.1.1 255.255.255.0
```

**Expected AI Response:**
```json
{
  "case_id": "CASE-EX03",
  "root_cause": "Missing 'ip helper-address 10.1.1.50' relay configuration on interface Vlan20, dropping client broadcast DHCP DISCOVER packets at the router boundary.",
  "osi_layer": 7,
  "confidence": "high",
  "evidence": "Core-SW show run interface Vlan20 contains only 'ip address 192.168.20.1' and lacks 'ip helper-address' while DHCP server is in a different subnet (10.1.1.50).",
  "next_command": "show ip interface Vlan20 | include Helper",
  "fix_steps": [
    "configure terminal",
    "interface Vlan20",
    "ip helper-address 10.1.1.50",
    "end",
    "write memory"
  ],
  "reasoning_summary": "Routers do not forward Layer 2 broadcast packets by default. An ip helper-address relay agent is required on the client SVI to unicast DHCP requests to remote DHCP servers."
}
```
