/**
 * NetSage AI - Unified Dashboard Engine & Live Terminal Simulator
 */

// Dataset Definition: 32 complete benchmark cases with ground truth, rules, AI outputs, and HITL verdicts
const DATASET = [
  {
    case_id: "CASE-001",
    tag: "VLAN",
    layer: 2,
    severity: "High",
    symptom: "Broadcast traffic leaking and CDP error logs between Dist-SW1 and Dist-SW2 across trunk link Gi0/1.",
    expected_fault: "Native VLAN mismatch on 802.1Q trunk link Gi0/1 (Dist-SW1 Native 10 vs Dist-SW2 Native 20).",
    show_output: `Dist-SW1# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      10

Dist-SW1# show log | include %CDP-4-NATIVE_VLAN_MISMATCH
%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (10), with Dist-SW2 GigabitEthernet0/1 (20).

Dist-SW2# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      20`,
    rule_verdict: "FLAGGED",
    rule_finding: "Native VLAN mismatch on trunk link GigabitEthernet0/1 (Local 10 vs Remote 20).",
    ai_cause: "802.1Q trunk Native VLAN mismatch between Dist-SW1 (Native VLAN 10) and Dist-SW2 (Native VLAN 20) on interface Gi0/1.",
    ai_conf: "high",
    ai_evidence: "Dist-SW1# show log: '%CDP-4-NATIVE_VLAN_MISMATCH' and 'show interfaces trunk' shows Native vlan 10.",
    ai_fix: ["configure terminal", "interface GigabitEthernet0/1", "switchport trunk native vlan 20", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Accurate diagnosis. CDP syslog evidence clearly cited. Fix commands correctly align native VLAN.",
    human_edits: "None"
  },
  {
    case_id: "CASE-002",
    tag: "VLAN",
    layer: 2,
    severity: "Medium",
    symptom: "New workstations connected to Access-SW1 port Gi0/5 cannot communicate on Engineering VLAN 50.",
    expected_fault: "Access port Gi0/5 assigned to VLAN 50, but VLAN 50 does not exist in vlan.dat, marking port Inactive.",
    show_output: `Access-SW1# show interfaces GigabitEthernet0/5 switchport
Access Mode VLAN: 50 (Inactive)

Access-SW1# show vlan brief
VLAN Name                             Status    Ports
1    default                          active    Gi0/1-4
10   Sales                            active    Gi0/6-7`,
    rule_verdict: "FLAGGED",
    rule_finding: "Access port assigned to VLAN 50 (Inactive), missing from VLAN database.",
    ai_cause: "Access port Gi0/5 is assigned to VLAN 50, but VLAN 50 does not exist in the switch VLAN database, marking port Inactive.",
    ai_conf: "high",
    ai_evidence: "Access Mode VLAN: 50 (Inactive) and 'show vlan brief' lists only VLANs 1, 10, 20, 30 with VLAN 50 absent.",
    ai_fix: ["configure terminal", "vlan 50", "name Engineering", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Correctly identified inactive access VLAN due to missing vlan database entry.",
    human_edits: "None"
  },
  {
    case_id: "CASE-003",
    tag: "VLAN",
    layer: 2,
    severity: "High",
    symptom: "IP phones in Voice VLAN 40 cannot reach the Call Manager server through core uplink Gi0/24.",
    expected_fault: "VLAN 40 (Voice) is pruned from trunk allowed list on interface Gi0/24 (only 10,20,30 allowed).",
    show_output: `Access-SW2# show interfaces Gi0/24 trunk
Port        Vlans allowed on trunk
Gi0/24      10,20,30

Access-SW2# show run interface Gi0/24
 switchport trunk allowed vlan 10,20,30`,
    rule_verdict: "FLAGGED",
    rule_finding: "Required VLAN 40 is missing from trunk allowed list (10,20,30).",
    ai_cause: "VLAN 40 (Voice) is pruned from the trunk allowed list on uplink interface Gi0/24.",
    ai_conf: "high",
    ai_evidence: "switchport trunk allowed vlan 10,20,30 on Gi0/24 (VLAN 40 missing).",
    ai_fix: ["configure terminal", "interface GigabitEthernet0/24", "switchport trunk allowed vlan add 40", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Correctly spotted missing VLAN 40 in trunk allowed list.",
    human_edits: "None"
  },
  {
    case_id: "CASE-004",
    tag: "Wireless/L2",
    layer: 2,
    severity: "High",
    symptom: "Finance PC connected to Access Switch port Gi0/12 suddenly lost network connectivity; port is amber.",
    expected_fault: "Port Gi0/12 placed into err-disabled state by STP BPDU Guard after receiving unauthorized BPDUs.",
    show_output: `Acc-SW3# show interfaces GigabitEthernet0/12 status
Gi0/12    Finance_PC_12      err-disabled 10

Acc-SW3# show log | include %SPANTREE-2-BLOCK_BPDUGUARD
%SPANTREE-2-BLOCK_BPDUGUARD: Received BPDU on port Gi0/12 with BPDU Guard enabled. Disabling port.`,
    rule_verdict: "FLAGGED",
    rule_finding: "Interface Gi0/12 entered err-disabled state due to BPDU Guard.",
    ai_cause: "Interface Gi0/12 was placed into err-disabled state by STP BPDU Guard upon receiving unexpected BPDUs on a PortFast edge port.",
    ai_conf: "high",
    ai_evidence: "%SPANTREE-2-BLOCK_BPDUGUARD: Received BPDU on port Gi0/12 with BPDU Guard enabled.",
    ai_fix: ["configure terminal", "interface GigabitEthernet0/12", "shutdown", "no shutdown", "end"],
    human_verdict: "Accepted",
    reviewer_notes: "Evidence correctly references BPDU Guard error. Remediation sequence is safe.",
    human_edits: "None"
  },
  {
    case_id: "CASE-005",
    tag: "Routing",
    layer: 3,
    severity: "High",
    symptom: "Web Server SRV-01 (192.168.10.50) cannot reach default gateway 192.168.10.1.",
    expected_fault: "Subnet mask mismatch on server SRV-01: configured with /28 (255.255.255.240) isolating gateway 192.168.10.1.",
    show_output: `SRV-01# ipconfig /all
   IPv4 Address. . . . . : 192.168.10.50
   Subnet Mask . . . . . : 255.255.255.240
   Default Gateway . . . : 192.168.10.1

Core-RTR# show ip interface Gi0/0
  Internet address is 192.168.10.1/24`,
    rule_verdict: "FLAGGED",
    rule_finding: "Subnet mask mismatch: Host /28 (192.168.10.48-63) excludes Gateway 192.168.10.1/24.",
    ai_cause: "Subnet mask mismatch on server SRV-01: configured with /28 (255.255.255.240) isolating it from router gateway 192.168.10.1.",
    ai_conf: "high",
    ai_evidence: "SRV-01 Subnet Mask: 255.255.255.240 vs Router Gi0/0 Internet address 192.168.10.1/24.",
    ai_fix: ["netsh interface ipv4 set address name=\"Local Area Connection\" static 192.168.10.50 255.255.255.0 192.168.10.1"],
    human_verdict: "Accepted",
    reviewer_notes: "Accurately calculated subnet boundary error for /28 mask on 192.168.10.50.",
    human_edits: "None"
  },
  {
    case_id: "CASE-006",
    tag: "Routing",
    layer: 3,
    severity: "High",
    symptom: "Database Server DB-01 cannot communicate with external API endpoints or other subnets.",
    expected_fault: "Default gateway mismatch on DB-01: configured with 10.10.30.1 (VLAN 30 gateway) instead of 10.10.20.1.",
    show_output: `DB-01# ifconfig eth0
inet 10.10.20.15  netmask 255.255.255.0
DB-01# ip route show
default via 10.10.30.1 dev eth0

Core-RTR# show ip interface brief | include Vlan
Vlan20                 10.10.20.1      YES manual up                    up
Vlan30                 10.10.30.1      YES manual up                    up`,
    rule_verdict: "FLAGGED",
    rule_finding: "Default gateway 10.10.30.1 is not in host's local subnet 10.10.20.0/24.",
    ai_cause: "Host DB-01 default gateway is misconfigured with IP 10.10.30.1 (VLAN 30 SVI) instead of 10.10.20.1 (local VLAN 20 SVI).",
    ai_conf: "high",
    ai_evidence: "DB-01 eth0 inet 10.10.20.15 netmask 255.255.255.0 with default via 10.10.30.1.",
    ai_fix: ["sudo ip route del default", "sudo ip route add default via 10.10.20.1 dev eth0"],
    human_verdict: "Accepted",
    reviewer_notes: "Correctly identified default gateway off-subnet pointing to adjacent VLAN SVI.",
    human_edits: "None"
  },
  {
    case_id: "CASE-007",
    tag: "Routing",
    layer: 3,
    severity: "High",
    symptom: "OSPF neighbor adjacency between Core-R1 and Dist-R2 is stuck in EXSTART/EXCHANGE state.",
    expected_fault: "OSPF interface MTU mismatch on link Gi0/0 (Core-R1 MTU 1500 vs Dist-R2 MTU 1400), causing DBD exchange failure.",
    show_output: `Core-R1# show ip ospf neighbor
192.168.2.2       1   EXSTART/  -     00:00:33    10.0.0.2        GigabitEthernet0/0

Core-R1# show ip interface Gi0/0 | include MTU
  MTU is 1500 bytes

Dist-R2# show ip interface Gi0/0 | include MTU
  MTU is 1400 bytes`,
    rule_verdict: "FLAGGED",
    rule_finding: "OSPF MTU mismatch between neighbors: Local MTU 1500 bytes vs Remote MTU 1400 bytes.",
    ai_cause: "OSPF authentication MD5 key mismatch between Core-R1 and Dist-R2 on transit link Gi0/0.",
    ai_conf: "high",
    ai_evidence: "Core-R1 show ip ospf neighbor stuck in EXSTART.",
    ai_fix: ["configure terminal", "interface GigabitEthernet0/0", "ip ospf message-digest-key 1 md5 Cisco123"],
    human_verdict: "Rejected",
    reviewer_notes: "AI hallucinated authentication failure based on EXSTART neighbor state without verifying MTU parameters in show ip interface.",
    human_edits: "Actual Fault: OSPF MTU mismatch (R1 MTU 1500 vs R2 MTU 1400). Remediated with 'ip mtu 1500'."
  },
  {
    case_id: "CASE-008",
    tag: "Routing",
    layer: 3,
    severity: "High",
    symptom: "Branch office users can ping local servers but cannot access public Internet websites (e.g. 8.8.8.8).",
    expected_fault: "Missing default static route (0.0.0.0/0) to ISP Gateway 203.0.113.1 on Branch-RTR.",
    show_output: `Branch-RTR# show ip route
Gateway of last resort is not set

Branch-RTR# ping 8.8.8.8
Success rate is 0 percent (0/5)`,
    rule_verdict: "FLAGGED",
    rule_finding: "Missing default route (0.0.0.0/0) to ISP gateway; Gateway of last resort is not set.",
    ai_cause: "Missing default static route (0.0.0.0/0) to ISP Gateway 203.0.113.1 on Branch-RTR; Gateway of last resort is not set.",
    ai_conf: "high",
    ai_evidence: "Branch-RTR show ip route shows 'Gateway of last resort is not set' and ping to 8.8.8.8 fails.",
    ai_fix: ["configure terminal", "ip route 0.0.0.0 0.0.0.0 203.0.113.1", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Confirmed missing 0.0.0.0/0 static route to ISP gateway.",
    human_edits: "None"
  },
  {
    case_id: "CASE-009",
    tag: "Routing",
    layer: 3,
    severity: "Medium",
    symptom: "HQ-RTR1 cannot form OSPF adjacency with Core-RTR2 across point-to-point link Gi0/2.",
    expected_fault: "Interface GigabitEthernet0/2 configured as passive-interface under OSPF process 1.",
    show_output: `HQ-RTR1# show ip ospf interface Gi0/2
  No Hellos (Passive interface)
HQ-RTR1# show run | section router ospf
 passive-interface GigabitEthernet0/2`,
    rule_verdict: "FLAGGED",
    rule_finding: "OSPF passive-interface configured on link Gi0/2, suppressing Hello packets.",
    ai_cause: "Core link GigabitEthernet0/2 is configured as a passive-interface under OSPF process 1, suppressing Hello transmissions.",
    ai_conf: "high",
    ai_evidence: "show ip ospf interface Gi0/2 shows 'No Hellos (Passive interface)'.",
    ai_fix: ["configure terminal", "router ospf 1", "no passive-interface GigabitEthernet0/2", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Correctly identified passive-interface under router ospf 1.",
    human_edits: "None"
  },
  {
    case_id: "CASE-010",
    tag: "Routing",
    layer: 3,
    severity: "High",
    symptom: "BGP peering between Enterprise Edge router and ISP Border Router remains in Active/Idle state.",
    expected_fault: "BGP AS number mismatch: Edge-RTR configured neighbor with remote-as 65510 instead of ISP AS 65500.",
    show_output: `Edge-RTR# show ip bgp summary
198.51.100.1    4        65510       0       0        1    0    0 00:14:22 Active

ISP-RTR# show run | section router bgp
router bgp 65500`,
    rule_verdict: "FLAGGED",
    rule_finding: "BGP remote-as mismatch: Configured remote-as 65510 vs ISP router bgp 65500.",
    ai_cause: "eBGP peering session fails due to remote-as number mismatch (Edge-RTR remote-as 65510 vs ISP AS 65500).",
    ai_conf: "high",
    ai_evidence: "Edge-RTR configured 'neighbor 198.51.100.1 remote-as 65510' vs ISP 'router bgp 65500'.",
    ai_fix: ["configure terminal", "router bgp 65001", "no neighbor 198.51.100.1 remote-as 65510", "neighbor 198.51.100.1 remote-as 65500", "end", "clear ip bgp 198.51.100.1"],
    human_verdict: "Accepted",
    reviewer_notes: "BGP remote-as mismatch correctly isolated.",
    human_edits: "None"
  },
  {
    case_id: "CASE-011",
    tag: "Routing",
    layer: 3,
    severity: "Medium",
    symptom: "Static route to remote subnet 172.20.0.0/16 is not present in the routing table.",
    expected_fault: "Next-hop IP 10.254.1.1 is unreachable and has no route in the RIB (recursive routing failure).",
    show_output: `Edge-RTR# show run | include ip route
ip route 172.20.0.0 255.255.0.0 10.254.1.1
Edge-RTR# show ip route 10.254.1.1
% Network not in table`,
    rule_verdict: "FLAGGED",
    rule_finding: "Recursive route lookup failure: Static route next-hop 10.254.1.1 is not in table.",
    ai_cause: "Static route next-hop IP 10.254.1.1 is unreachable and has no route in the RIB (recursive routing failure).",
    ai_conf: "high",
    ai_evidence: "ip route 172.20.0.0 255.255.0.0 10.254.1.1 configured, but 'show ip route 10.254.1.1' returns '% Network not in table'.",
    ai_fix: ["configure terminal", "ip route 172.20.0.0 255.255.0.0 10.100.1.2", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Valid diagnosis. Recursive lookup failure prevented static route installation.",
    human_edits: "None"
  },
  {
    case_id: "CASE-012",
    tag: "NAT",
    layer: 3,
    severity: "High",
    symptom: "Internal clients cannot access Internet; NAT translations table is completely empty.",
    expected_fault: "NAT inside/outside interface statements are inverted (LAN has outside, WAN has inside).",
    show_output: `GW-RTR# show run interface Gi0/0
interface GigabitEthernet0/0 (LAN)
 ip nat outside

GW-RTR# show run interface Gi0/1
interface GigabitEthernet0/1 (WAN)
 ip nat inside

GW-RTR# show ip nat translations
(empty)`,
    rule_verdict: "FLAGGED",
    rule_finding: "NAT interface direction is inverted: LAN is ip nat outside, WAN is ip nat inside.",
    ai_cause: "ACL 1 denies internal outbound NAT traffic, blocking translations on Gi0/1.",
    ai_conf: "high",
    ai_evidence: "NAT translations table is empty.",
    ai_fix: ["configure terminal", "access-list 1 permit 192.168.1.0 0.0.0.255"],
    human_verdict: "Rejected",
    reviewer_notes: "AI blamed standard ACL permit logic instead of inspecting interface nat tags. Corrected with 'no ip nat outside' on LAN.",
    human_edits: "Actual Fault: NAT inside/outside interface inverted on Gi0/0 (LAN has outside) and Gi0/1 (WAN has inside)."
  },
  {
    case_id: "CASE-013",
    tag: "NAT",
    layer: 3,
    severity: "High",
    symptom: "Branch office PCs in 192.168.20.0/24 cannot reach Internet; NAT stats show 0 hits.",
    expected_fault: "NAT ACL 10 permits 192.168.10.0/24 instead of active LAN subnet 192.168.20.0/24.",
    show_output: `Branch-RTR# show access-lists 10
Standard IP access list 10
    10 permit 192.168.10.0, wildcard bits 0.0.0.255 (0 matches)

Branch-RTR# show ip interface Gi0/0
  Internet address is 192.168.20.1/24`,
    rule_verdict: "FLAGGED",
    rule_finding: "NAT ACL permits 192.168.10.0 but local LAN is 192.168.20.1 (Hits: 0, Misses: 142).",
    ai_cause: "NAT Access-List 10 permits 192.168.10.0/24 instead of the active LAN subnet 192.168.20.0/24.",
    ai_conf: "high",
    ai_evidence: "show access-lists 10: 'permit 192.168.10.0 (0 matches)' vs Gi0/0 IP 192.168.20.1/24.",
    ai_fix: ["configure terminal", "access-list 10 permit 192.168.20.0 0.0.0.255", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Correctly identified subnet mismatch in ACL 10.",
    human_edits: "None"
  },
  {
    case_id: "CASE-014",
    tag: "NAT",
    layer: 3,
    severity: "High",
    symptom: "Outbound Internet connections drop intermittently; ISP complains of ARP IP conflicts on 198.51.100.1.",
    expected_fault: "Dynamic NAT pool CORP_POOL includes 198.51.100.1, which is the upstream ISP default gateway IP.",
    show_output: `Edge-RTR# show run | section ip nat pool
ip nat pool CORP_POOL 198.51.100.1 198.51.100.6 netmask 255.255.255.248
ip route 0.0.0.0 0.0.0.0 198.51.100.1`,
    rule_verdict: "FLAGGED",
    rule_finding: "Dynamic NAT pool includes IP 198.51.100.1, which conflicts with default gateway.",
    ai_cause: "Dynamic NAT pool CORP_POOL range (198.51.100.1-6) includes IP 198.51.100.1, which is the upstream ISP gateway IP.",
    ai_conf: "high",
    ai_evidence: "ip nat pool CORP_POOL 198.51.100.1 198.51.100.6 conflicts with default route 198.51.100.1.",
    ai_fix: ["configure terminal", "ip nat pool CORP_POOL 198.51.100.3 198.51.100.6 netmask 255.255.255.248", "end", "clear ip nat translation *"],
    human_verdict: "Accepted",
    reviewer_notes: "High severity ARP conflict correctly spotted in NAT pool starting address.",
    human_edits: "None"
  },
  {
    case_id: "CASE-015",
    tag: "NAT",
    layer: 3,
    severity: "Medium",
    symptom: "External customers cannot connect to public DMZ HTTPS server; public DNS resolves to 203.0.113.205.",
    expected_fault: "Static 1-to-1 NAT IP typo: mapped inside server to 203.0.113.250 instead of public DNS IP 203.0.113.205.",
    show_output: `Edge-GW# show run | include ip nat inside source static
ip nat inside source static 192.168.100.10 203.0.113.250

External-Client# nslookup secure.example.com
Address: 203.0.113.205`,
    rule_verdict: "FLAGGED",
    rule_finding: "Static NAT outside IP (203.0.113.250) does not match public DNS A-record (203.0.113.205).",
    ai_cause: "Static 1-to-1 NAT configuration typo: mapped inside server 192.168.100.10 to 203.0.113.250 instead of 203.0.113.205.",
    ai_conf: "medium",
    ai_evidence: "ip nat inside source static 192.168.100.10 203.0.113.250 vs DNS query 203.0.113.205.",
    ai_fix: ["configure terminal", "ip nat inside source static 192.168.100.10 203.0.113.205", "end", "write memory"],
    human_verdict: "Edited",
    reviewer_notes: "AI identified transposed digits (.250 vs .205) but forgot 'no ip nat inside source static' in fix steps.",
    human_edits: "Adjusted fix step to remove old translation before adding correct one to prevent orphaned NAT table entry."
  },
  {
    case_id: "CASE-016",
    tag: "DHCP",
    layer: 7,
    severity: "High",
    symptom: "Workstations on Sales VLAN 20 are unable to obtain IP addresses and fall back to APIPA (169.254.x.x).",
    expected_fault: "Missing 'ip helper-address 10.1.1.50' under interface Vlan20 on Core-SW1.",
    show_output: `Core-SW1# show run interface Vlan20
interface Vlan20
 ip address 192.168.20.1 255.255.255.0
 no ip redirects

Core-SW1# show run interface Vlan10
interface Vlan10
 ip address 10.1.1.1 255.255.255.0 (DHCP Server is 10.1.1.50)`,
    rule_verdict: "FLAGGED",
    rule_finding: "Missing 'ip helper-address' on interface Vlan20 for cross-subnet DHCP.",
    ai_cause: "Missing 'ip helper-address 10.1.1.50' relay configuration on interface Vlan20 on Core-SW1.",
    ai_conf: "high",
    ai_evidence: "interface Vlan20 lacks 'ip helper-address' while DHCP server is located at 10.1.1.50.",
    ai_fix: ["configure terminal", "interface Vlan20", "ip helper-address 10.1.1.50", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Layer 3 relay agent requirement identified accurately for cross-VLAN DHCP.",
    human_edits: "None"
  },
  {
    case_id: "CASE-017",
    tag: "DHCP",
    layer: 7,
    severity: "High",
    symptom: "Guests in conference room cannot connect to Guest Wi-Fi; DHCP offers are not received.",
    expected_fault: "DHCP address pool GUEST_WIFI is completely exhausted (51/51 leased addresses).",
    show_output: `Guest-RTR# show ip dhcp pool GUEST_WIFI
 Utilization mark (high/low)    : 100 / 0
 Total addresses                : 51
 Leased addresses               : 51

Guest-RTR# show log | include %DHCPD-4-DECLINE
%DHCPD-4-DECLINE: Address pool GUEST_WIFI is full`,
    rule_verdict: "FLAGGED",
    rule_finding: "DHCP address pool 'GUEST_WIFI' is 100% full with 0 remaining leases.",
    ai_cause: "DHCP address pool GUEST_WIFI is 100% full (51/51 leases allocated), rejecting new guest client lease requests.",
    ai_conf: "high",
    ai_evidence: "Utilization mark: 100 / 0, Total: 51, Leased: 51, and %DHCPD-4-DECLINE pool is full.",
    ai_fix: ["configure terminal", "ip dhcp pool GUEST_WIFI", "lease 0 2 0", "end", "clear ip dhcp binding *"],
    human_verdict: "Accepted",
    reviewer_notes: "Correctly diagnosed pool exhaustion from utilization mark and decline syslogs.",
    human_edits: "None"
  },
  {
    case_id: "CASE-018",
    tag: "DHCP",
    layer: 7,
    severity: "High",
    symptom: "Employee laptops suddenly received default gateway 192.168.88.1 and lost access to intranet.",
    expected_fault: "Rogue DHCP server on Gi0/8 distributing rogue leases (192.168.88.0/24) because DHCP Snooping is disabled.",
    show_output: `Employee-PC# ipconfig /all
   Default Gateway . . . . . . . . . : 192.168.88.1
   DHCP Server . . . . . . . . . . . : 192.168.88.1

Access-SW1# show ip dhcp snooping
Switch DHCP snooping is disabled`,
    rule_verdict: "CLEAN",
    rule_finding: "All deterministic rules passed.",
    ai_cause: "DHCP server scope pool exhaustion on corporate core router.",
    ai_conf: "high",
    ai_evidence: "Laptops lost access to intranet resources.",
    ai_fix: ["configure terminal", "ip dhcp pool CORP", "network 10.10.10.0 255.255.255.0"],
    human_verdict: "Rejected",
    reviewer_notes: "AI misclassified symptom as local pool exhaustion rather than detecting rogue server offering rogue default gateway 192.168.88.1.",
    human_edits: "Actual Fault: Rogue DHCP server on Gi0/8 offering 192.168.88.0/24 leases; DHCP snooping is disabled."
  },
  {
    case_id: "CASE-019",
    tag: "DHCP",
    layer: 3,
    severity: "Medium",
    symptom: "Network printer and Executive PC experience intermittent connection drops; duplicate IP warnings in syslog.",
    expected_fault: "Duplicate IP conflict: static printer IP 192.168.1.25 not excluded in 'ip dhcp excluded-address'.",
    show_output: `Core-RTR# show log | include %IP-4-DUPADDR
%IP-4-DUPADDR: Duplicate address 192.168.1.25 on GigabitEthernet0/0, sourced by 50eb.7112.44bb and 0011.2233.4455

Core-RTR# show ip dhcp binding | include 192.168.1.25
192.168.1.25        0150.eb71.1244.bb       Automatic`,
    rule_verdict: "FLAGGED",
    rule_finding: "Duplicate IP address detected: 192.168.1.25 claimed simultaneously by PC and Printer.",
    ai_cause: "Duplicate IP address conflict: static printer IP 192.168.1.25 was not included in 'ip dhcp excluded-address' and was leased to a PC.",
    ai_conf: "high",
    ai_evidence: "Syslog '%IP-4-DUPADDR: Duplicate address 192.168.1.25' and 'ip dhcp binding' shows 192.168.1.25 leased.",
    ai_fix: ["configure terminal", "ip dhcp excluded-address 192.168.1.1 192.168.1.50", "end", "clear ip dhcp binding 192.168.1.25"],
    human_verdict: "Accepted",
    reviewer_notes: "Duplicate IP syslog and DHCP binding overlap correctly correlated.",
    human_edits: "None"
  },
  {
    case_id: "CASE-020",
    tag: "DHCP",
    layer: 7,
    severity: "Low",
    symptom: "Default gateway 10.50.0.254 becomes unresponsive; host ARP points to a random workstation MAC.",
    expected_fault: "Gateway IP 10.50.0.254 omitted from 'ip dhcp excluded-address', leased to a client.",
    show_output: `Core-SW# show run | section ip dhcp
ip dhcp excluded-address 10.50.0.1 10.50.0.50
default-router 10.50.0.254

Core-SW# show ip dhcp binding | include 10.50.0.254
10.50.0.254         01cc.4477.8899.aa       Automatic`,
    rule_verdict: "FLAGGED",
    rule_finding: "Default gateway IP 10.50.0.254 is leased by DHCP server to a dynamic client.",
    ai_cause: "DHCP server leased default gateway IP 10.50.0.254 to a client because 'ip dhcp excluded-address' only covered .1 to .50.",
    ai_conf: "medium",
    ai_evidence: "default-router 10.50.0.254 while excluded range is 10.50.0.1-50; 'show ip dhcp binding' shows 10.50.0.254 leased.",
    ai_fix: ["configure terminal", "ip dhcp excluded-address 10.50.0.254", "end"],
    human_verdict: "Edited",
    reviewer_notes: "AI diagnosed missing excluded address but omitted clearing the active hijacked lease.",
    human_edits: "Changed fix steps to include 'clear ip dhcp binding 10.50.0.254' so client is forced to release the gateway IP immediately."
  },
  {
    case_id: "CASE-021",
    tag: "ACL",
    layer: 3,
    severity: "High",
    symptom: "Finance hosts in 192.168.10.0/24 cannot reach internal Accounting SQL server at 192.168.30.50.",
    expected_fault: "Standard ACL 10 applied outbound on Gi0/3 explicitly denies source subnet 192.168.10.0/24.",
    show_output: `Core-RTR# show access-lists 10
Standard IP access list 10
    10 deny   192.168.10.0, wildcard bits 0.0.0.255 (450 matches)
    20 permit any (1200 matches)

Core-RTR# show run interface Gi0/3
 ip access-group 10 out`,
    rule_verdict: "FLAGGED",
    rule_finding: "Standard ACL explicitly denies traffic from subnet 192.168.10.0 (450 matches).",
    ai_cause: "Standard ACL 10 applied outbound on interface Gi0/3 explicitly denies source subnet 192.168.10.0/24 from reaching Accounting VLAN.",
    ai_conf: "high",
    ai_evidence: "show access-lists 10: '10 deny 192.168.10.0 (450 matches)' on interface Gi0/3.",
    ai_fix: ["configure terminal", "interface GigabitEthernet0/3", "no ip access-group 10 out", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Identified standard ACL drop matches on inter-VLAN interface.",
    human_edits: "None"
  },
  {
    case_id: "CASE-022",
    tag: "ACL",
    layer: 4,
    severity: "High",
    symptom: "Internal users can initiate TCP web connections to external servers, but pages time out.",
    expected_fault: "Inbound ACL INBOUND_FILTER on WAN interface lacks 'permit tcp any any established', dropping return SYN-ACKs.",
    show_output: `Edge-RTR# show access-lists INBOUND_FILTER
Extended IP access list INBOUND_FILTER
    10 permit udp any any eq domain
    20 permit icmp any any echo-reply
    30 deny ip any any (18934 matches)`,
    rule_verdict: "FLAGGED",
    rule_finding: "Inbound ACL is missing 'permit tcp any any established' (18934 drop matches).",
    ai_cause: "Inbound ACL INBOUND_FILTER on WAN interface Gi0/1 lacks 'permit tcp any any established', dropping return SYN-ACK web traffic.",
    ai_conf: "high",
    ai_evidence: "show access-lists INBOUND_FILTER shows '30 deny ip any any (18934 matches)' with no TCP established permit rule.",
    ai_fix: ["configure terminal", "ip access-list extended INBOUND_FILTER", "15 permit tcp any any established", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Critical stateful inspection omission identified; cited 18k+ deny matches.",
    human_edits: "None"
  },
  {
    case_id: "CASE-023",
    tag: "ACL",
    layer: 4,
    severity: "High",
    symptom: "Branch office cannot resolve external domain names; nslookup queries to public DNS 8.8.8.8 time out.",
    expected_fault: "ACL SEC_FILTER only permits TCP port 53 ('eq domain') but omits UDP port 53.",
    show_output: `Branch-RTR# show access-lists SEC_FILTER
Extended IP access list SEC_FILTER
    10 permit tcp 192.168.1.0 0.0.0.255 any eq www
    20 permit tcp 192.168.1.0 0.0.0.255 any eq 443
    30 permit tcp 192.168.1.0 0.0.0.255 any eq domain
    40 deny ip any any (532 matches)`,
    rule_verdict: "FLAGGED",
    rule_finding: "ACL SEC_FILTER only permits TCP port 53 but omits UDP port 53 for DNS.",
    ai_cause: "ACL SEC_FILTER on WAN interface Gi0/0 permits TCP port 53 ('eq domain') but omits UDP port 53, blocking standard DNS queries.",
    ai_conf: "high",
    ai_evidence: "show access-lists SEC_FILTER has '30 permit tcp ... eq domain' followed by '40 deny ip any any (532 matches)'; UDP 53 is missing.",
    ai_fix: ["configure terminal", "ip access-list extended SEC_FILTER", "35 permit udp 192.168.1.0 0.0.0.255 any eq domain", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Sharp technical catch: DNS queries default to UDP 53; ACL permitted only TCP 53.",
    human_edits: "None"
  },
  {
    case_id: "CASE-024",
    tag: "ACL",
    layer: 3,
    severity: "Medium",
    symptom: "Guest users in VLAN 90 can ping and browse internal corporate servers in VLAN 10 despite restrictive ACL.",
    expected_fault: "ACL BLOCK_GUEST was applied outbound on WAN interface Gi0/1 instead of inbound on interface Vlan90.",
    show_output: `Core-SW# show access-lists BLOCK_GUEST
    10 deny ip 172.16.90.0 0.0.0.255 172.16.10.0 0.0.0.255

Core-SW# show run interface Gi0/1 (WAN)
 ip access-group BLOCK_GUEST out

Core-SW# show run interface Vlan90
 ip address 172.16.90.1 255.255.255.0 (No access-group)`,
    rule_verdict: "FLAGGED",
    rule_finding: "ACL BLOCK_GUEST was applied outbound on WAN interface Gi0/1 rather than inbound on Vlan90.",
    ai_cause: "ACL BLOCK_GUEST was misapplied outbound on WAN interface Gi0/1 instead of inbound on interface Vlan90, leaving inter-VLAN guest traffic uninspected.",
    ai_conf: "medium",
    ai_evidence: "interface Gi0/1 has 'ip access-group BLOCK_GUEST out' while interface Vlan90 has no access-group applied.",
    ai_fix: ["configure terminal", "interface GigabitEthernet0/1", "no ip access-group BLOCK_GUEST out", "interface Vlan90", "ip access-group BLOCK_GUEST in", "end", "write memory"],
    human_verdict: "Edited",
    reviewer_notes: "AI diagnosis correct; refined verification command for operational validation.",
    human_edits: "Refined next_command to 'show ip interface Vlan90' to verify access-group attachment."
  },
  {
    case_id: "CASE-025",
    tag: "DNS",
    layer: 7,
    severity: "High",
    symptom: "Domain workstation logins fail with 'Domain controller cannot be contacted' after server maintenance.",
    expected_fault: "DHCP pool CORP_USERS configured with decommissioned DNS server IP 10.10.1.20 instead of 10.10.1.50.",
    show_output: `Core-RTR# show run | section ip dhcp pool
 dns-server 10.10.1.20

Core-RTR# ping 10.10.1.20
Success rate is 0 percent (0/5)
Core-RTR# ping 10.10.1.50
Success rate is 100 percent (5/5)`,
    rule_verdict: "FLAGGED",
    rule_finding: "Configured DNS server 10.10.1.20 is unreachable (0% ping success rate).",
    ai_cause: "DHCP pool CORP_USERS is configured with decommissioned DNS server IP 10.10.1.20 (which fails ICMP ping) instead of active server 10.10.1.50.",
    ai_conf: "high",
    ai_evidence: "DHCP pool shows 'dns-server 10.10.1.20'; Ping to 10.10.1.20 is 0% success while ping to 10.10.1.50 is 100% success.",
    ai_fix: ["configure terminal", "ip dhcp pool CORP_USERS", "dns-server 10.10.1.50", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Stale DNS server IP in DHCP scope verified against 0% ICMP ping rate.",
    human_edits: "None"
  },
  {
    case_id: "CASE-026",
    tag: "DNS",
    layer: 7,
    severity: "Medium",
    symptom: "Branch office PCs cannot resolve internal intranet URLs (e.g. portal.corp.local) but public sites resolve.",
    expected_fault: "Split-brain DNS misconfiguration: Branch-GW name-servers set exclusively to public resolvers (8.8.8.8) with no conditional forwarder for .corp.local.",
    show_output: `Branch-GW# show run | include ip dns
ip dns server
ip dns forwarding
ip name-server 8.8.8.8

Branch-GW# show hosts
Default domain is corp.local`,
    rule_verdict: "CLEAN",
    rule_finding: "All deterministic rules passed.",
    ai_cause: "DNS Server process on Branch-GW has crashed.",
    ai_conf: "medium",
    ai_evidence: "Branch office PCs cannot resolve internal intranet URLs.",
    ai_fix: ["configure terminal", "no ip dns server", "ip dns server"],
    human_verdict: "Rejected",
    reviewer_notes: "AI hallucinated a service crash instead of analyzing public vs internal domain name-server forwarding.",
    human_edits: "Actual Fault: Split-brain DNS configuration (no conditional forwarder for .corp.local zone to internal DNS 10.0.0.5)."
  },
  {
    case_id: "CASE-027",
    tag: "DNS",
    layer: 4,
    severity: "Medium",
    symptom: "Workstations fail to resolve DNS records for DNSSEC domains (large UDP responses > 1400 bytes) across IPsec VPN.",
    expected_fault: "Path MTU black hole on IPsec Tunnel0 (MTU 1400): 'no ip unreachables' suppresses ICMP Fragmentation Needed.",
    show_output: `Branch-RTR# show interfaces Tunnel0
  MTU 1400 bytes
  ICMP unreachables are never sent

Branch-RTR# show run interface Tunnel0
 no ip unreachables`,
    rule_verdict: "CLEAN",
    rule_finding: "All deterministic rules passed.",
    ai_cause: "Path MTU black hole on IPsec Tunnel0 (MTU 1400): 'no ip unreachables' suppresses ICMP Fragmentation Needed packets for large UDP DNS responses.",
    ai_conf: "medium",
    ai_evidence: "Tunnel0 MTU is 1400 bytes, 'ICMP unreachables are never sent', and 'no ip unreachables' configured on Tunnel0.",
    ai_fix: ["configure terminal", "interface Tunnel0", "ip unreachables", "end", "write memory"],
    human_verdict: "Edited",
    reviewer_notes: "AI correctly identified MTU drop but missed the ICMP unreachables suppression nuance.",
    human_edits: "Added 'ip tcp adjust-mss 1360' and 'ip unreachables' to remediation steps."
  },
  {
    case_id: "CASE-028",
    tag: "Wireless/L2",
    layer: 1,
    severity: "Medium",
    symptom: "File transfers between File Server and clients are extremely sluggish with excessive packet drops and collisions.",
    expected_fault: "Duplex mismatch on Gi0/3: Switch auto-negotiated to Half-Duplex against hardcoded Full-Duplex server NIC.",
    show_output: `Switch-1# show interfaces GigabitEthernet0/3
  Half-duplex, 100Mb/s
  49102 input errors, 48920 CRC
  38192 late collision, 18290 deferred`,
    rule_verdict: "FLAGGED",
    rule_finding: "Duplex mismatch detected: Half-duplex with 38192 late collisions and 48920 CRC errors.",
    ai_cause: "Duplex mismatch on switch port Gi0/3: Switch auto-negotiated to Half-Duplex against hardcoded Full-Duplex server NIC, causing late collisions.",
    ai_conf: "high",
    ai_evidence: "show interfaces Gi0/3 shows 'Half-duplex, 100Mb/s', '49102 input errors, 48920 CRC', and '38192 late collision'.",
    ai_fix: ["configure terminal", "interface GigabitEthernet0/3", "speed 100", "duplex full", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Classic IEEE 802.3 duplex autonegotiation failure correctly diagnosed from late collisions.",
    human_edits: "None"
  },
  {
    case_id: "CASE-029",
    tag: "Wireless/L2",
    layer: 2,
    severity: "High",
    symptom: "Conference room network jack stopped working when a second laptop was connected via a mini switch.",
    expected_fault: "Port Security violation on Gi0/7: maximum MAC limit of 1 was exceeded, placing port in err-disabled shutdown.",
    show_output: `Acc-SW1# show port-security interface Gi0/7
Port Status                : Secure-shutdown
Violation Mode             : Shutdown
Maximum MAC Addresses      : 1
Total MAC Addresses        : 1
Security Violation Count   : 1

Acc-SW1# show interfaces Gi0/7 status
Gi0/7     Conf_Room_Jack     err-disabled 10`,
    rule_verdict: "FLAGGED",
    rule_finding: "Port Security violation triggered by MAC 0025.90cd.e412:10 (Violation Count: 1).",
    ai_cause: "Port Security violation on Gi0/7: maximum MAC address limit of 1 was exceeded when a second device connected, placing the port in err-disabled shutdown.",
    ai_conf: "high",
    ai_evidence: "show port-security interface Gi0/7: 'Port Status: Secure-shutdown', 'Security Violation Count: 1'; interface status is 'err-disabled'.",
    ai_fix: ["configure terminal", "interface GigabitEthernet0/7", "shutdown", "no shutdown", "end"],
    human_verdict: "Accepted",
    reviewer_notes: "Port security err-disabled status and violation count correctly cited.",
    human_edits: "None"
  },
  {
    case_id: "CASE-030",
    tag: "Wireless/L2",
    layer: 2,
    severity: "High",
    symptom: "Users report MITM browser security warnings; traffic to default gateway is being intercepted.",
    expected_fault: "ARP Poisoning / Gateway MAC Spoofing attack by rogue host 192.168.1.199 because Dynamic ARP Inspection is disabled.",
    show_output: `Host-PC# arp -a
  192.168.1.1           a483-e721-99aa        dynamic
  192.168.1.199         a483-e721-99aa        dynamic

Core-SW# show ip arp inspection
Vlan 1 DAI is disabled`,
    rule_verdict: "FLAGGED",
    rule_finding: "ARP Poisoning / Gateway MAC spoofing detected: MAC a483.e721.99aa claims both gateway and host.",
    ai_cause: "ARP Cache Poisoning / Gateway MAC Spoofing attack by rogue host 192.168.1.199 (MAC a483-e721-99aa) because Dynamic ARP Inspection (DAI) is disabled.",
    ai_conf: "high",
    ai_evidence: "Host-PC arp -a shows both 192.168.1.1 and 192.168.1.199 mapped to physical address a483-e721-99aa; 'show ip arp inspection' shows Vlan 1 DAI is disabled.",
    ai_fix: ["configure terminal", "ip dhcp snooping", "ip dhcp snooping vlan 1", "ip arp inspection vlan 1", "end", "write memory"],
    human_verdict: "Accepted",
    reviewer_notes: "Security MITM attack accurately identified through identical MAC mapping on gateway and host.",
    human_edits: "None"
  },
  {
    case_id: "CASE-031",
    tag: "Wireless/L2",
    layer: 2,
    severity: "Medium",
    symptom: "Uplink port Gi0/24 on Core-SW connecting to newly added Distribution Switch entered blocking state.",
    expected_fault: "STP Root Guard on Core-SW Gi0/24 placed port into 'Root Inconsistent' state after receiving superior BPDUs with Priority 0.",
    show_output: `Core-SW# show spanning-tree inconsistentports
VLAN0001             GigabitEthernet0/24    Root Inconsistent

Dist-SW# show spanning-tree
  Root ID    Priority    0
             This bridge is the root`,
    rule_verdict: "FLAGGED",
    rule_finding: "STP Root Guard blocked the downstream port into 'Root Inconsistent' state.",
    ai_cause: "STP Root Guard on Core-SW Gi0/24 placed port into 'Root Inconsistent' blocking state after receiving superior BPDUs with Priority 0 from Dist-SW.",
    ai_conf: "high",
    ai_evidence: "show spanning-tree inconsistentports shows Gi0/24 'Root Inconsistent' and Dist-SW shows 'Root ID Priority 0, This bridge is the root'.",
    ai_fix: ["Dist-SW(config)# spanning-tree vlan 1-4094 priority 32768"],
    human_verdict: "Accepted",
    reviewer_notes: "STP Root Guard root-inconsistent state correctly tied to superior BPDU reception.",
    human_edits: "None"
  },
  {
    case_id: "CASE-032",
    tag: "Wireless/L2",
    layer: 4,
    severity: "Medium",
    symptom: "Branch Lightweight APs cannot register with the Wireless LAN Controller (WLC 10.200.1.5) across WAN.",
    expected_fault: "HQ Firewall ACL WAN_INSPECT blocks CAPWAP control/data UDP ports (5246/5247).",
    show_output: `HQ-Firewall# show access-lists WAN_INSPECT
    30 deny ip any host 10.200.1.5 (2481 matches)

Branch-AP# show capwap client status
Error: Discovery request to 10.200.1.5 timed out.`,
    rule_verdict: "FLAGGED",
    rule_finding: "Firewall ACL WAN_INSPECT blocks CAPWAP control/data UDP ports 5246/5247.",
    ai_cause: "HQ Firewall ACL WAN_INSPECT blocks CAPWAP control and data UDP ports (5246/5247) required for Branch Lightweight AP discovery with WLC 10.200.1.5.",
    ai_conf: "high",
    ai_evidence: "ACL WAN_INSPECT shows '30 deny ip any host 10.200.1.5 (2481 matches)' and AP status indicates 'Discovery request to 10.200.1.5 timed out'.",
    ai_fix: ["configure terminal", "ip access-list extended WAN_INSPECT", "25 permit udp any host 10.200.1.5 eq 5246", "26 permit udp any host 10.200.1.5 eq 5247", "end", "write memory"],
    human_verdict: "Edited",
    reviewer_notes: "AI classified as L2, but the actual fault is L4 firewall transport port filtering for CAPWAP UDP 5246/5247.",
    human_edits: "Classified primary OSI layer as Layer 4 (Transport / UDP ports) rather than Layer 2."
  }
];

const RAI_CASES = [
  {
    case_id: "CASE-007",
    title: "OSPF Adjacency Stuck in EXSTART vs. False Authentication Alarm",
    domain: "Layer 3 Routing (OSPF)",
    ai_said: "OSPF authentication MD5 key mismatch (Confidence: High)",
    ground_truth: "Interface MTU mismatch on link Gi0/0 (Core-R1 MTU 1500 vs Dist-R2 MTU 1400)",
    why_failed: "The AI over-indexed on the generic symptom 'OSPF neighbor state stuck' and hallucinated an authentication key mismatch without verifying the interface MTU lines in the show output.",
    risk: "Applying MD5 keys would have disrupted adjacent neighbor peerings across the enterprise without resolving the underlying MTU deadlock.",
    safeguard: "Implemented deterministic MTU parser in missing_route.py and updated prompt v2.0 to penalize confidence if exact MTU metrics are omitted."
  },
  {
    case_id: "CASE-012",
    title: "NAT Inside/Outside Inversion vs. False ACL Denial",
    domain: "Layer 3 NAT / PAT",
    ai_said: "ACL 1 denies internal outbound NAT traffic (Confidence: High)",
    ground_truth: "NAT interface tags were inverted: LAN interface had 'ip nat outside' and WAN had 'ip nat inside'",
    why_failed: "The AI assumed that an empty translation table must be caused by an ACL filter drop rather than inspecting interface NAT direction statements.",
    risk: "Modifying access control lists would not restore Internet traffic because the NAT engine only evaluates inside-to-outside translations.",
    safeguard: "Added deterministic interface tagging validation rule in nat_overload_pool.py and prompt guardrails requiring interface inspection."
  },
  {
    case_id: "CASE-018",
    title: "Rogue DHCP Server vs. False Scope Exhaustion",
    domain: "Layer 7 DHCP Application",
    ai_said: "Corporate DHCP pool exhaustion (Confidence: High)",
    ground_truth: "Rogue DHCP server on Gi0/8 offering 192.168.88.0/24 leases; DHCP snooping is disabled",
    why_failed: "Model saw 'lost access to intranet' and assumed the DHCP server had stopped issuing leases, missing that the client received an alien default gateway 192.168.88.1.",
    risk: "Expanding corporate pool size does nothing to stop the rogue server from winning the local Layer 2 broadcast race condition.",
    safeguard: "Added rogue gateway subnet comparison rule in duplicate_ip.py and few-shot examples for DHCP snooping."
  },
  {
    case_id: "CASE-026",
    title: "Split-Brain DNS Forwarding vs. False Service Crash",
    domain: "Layer 7 DNS Resolution",
    ai_said: "DNS Server process on Branch-GW has crashed (Confidence: Medium)",
    ground_truth: "Split-brain DNS configuration: name-server pointing to 8.8.8.8 with no forwarder for internal zone .corp.local to 10.0.0.5",
    why_failed: "Model associated resolution failure with total daemon death rather than inspecting the DNS name-server hierarchy.",
    risk: "Rebooting the gateway router causes unnecessary network downtime while failing to restore internal hostname resolution.",
    safeguard: "Added conditional DNS forwarding examples to few_shot_examples.md."
  },
  {
    case_id: "CASE-015",
    title: "Static NAT Typo & Orphaned Translation Prerequisite",
    domain: "Layer 3 NAT",
    ai_said: "Static 1-to-1 NAT configuration typo: mapped inside server to .250 instead of .205 (Confidence: Medium)",
    ground_truth: "Human verified diagnosis, but added required 'no ip nat inside source static' deletion step before adding new mapping.",
    why_failed: "In Cisco IOS, adding a second static translation for the same IP triggers a CLI conflict error (% already mapped).",
    risk: "Engineers executing the AI's script would encounter syntax errors and abort the change window.",
    safeguard: "Enforced mandatory state-negation commands in prompt fix_steps instructions."
  },
  {
    case_id: "CASE-020",
    title: "DHCP Gateway IP Hijack & Active Lease Flush",
    domain: "Layer 7 DHCP",
    ai_said: "Default gateway IP omitted from excluded-address range (Confidence: Medium)",
    ground_truth: "Human verified diagnosis, but added 'clear ip dhcp binding 10.50.0.254' to force immediate release.",
    why_failed: "Adding excluded-address prevents future leases but leaves the existing 7-day hijacked lease active on the client.",
    risk: "Default gateway remains unreachable until client lease naturally expires days later.",
    safeguard: "Updated standard remediation templates to include state cache flushes."
  }
];

/* ── Live Terminal Trace Simulation ── */
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const traceLines = [
  { text: '> netsage-diag --interactive', cls: 't-cmd', pause: 120 },
  { text: 'NetSage v2.0 — Cisco enterprise diagnostic assistant', cls: 't-label', pause: 200 },
  { text: '', pause: 40 },
  { text: '> Incident: CASE-007 (Core-R1 <-> Dist-R2 OSPF neighbor stuck in EXSTART)', cls: 't-val', pause: 60 },
  { text: '> Symptom: Adjacency fails to reach FULL state over link Gi0/0.', cls: 't-val', pause: 80 },
  { text: '> Show Evidence: show ip ospf neighbor, show ip interface Gi0/0', cls: 't-label', pause: 150 },
  { text: '', pause: 40 },
  { text: '■ Executing deterministic rule checker...', cls: 't-amber', pause: 300 },
  { text: '  [FLAGGED] OSPF MTU mismatch (Local 1500 vs Remote 1400 bytes)', cls: 't-red', pause: 250 },
  { text: '■ Querying evidence-grounded AI model...', cls: 't-amber', pause: 400 },
  { text: '', pause: 40 },
  { text: '┌─ Diagnosis ───────────────────────────────────────────────────', cls: 't-border', pause: 30 },
  { text: '│ Root cause: OSPF interface MTU mismatch on link Gi0/0', cls: 't-val', pause: 30 },
  { text: '│              drops DBD packets exceeding 1400 bytes', cls: 't-val', pause: 30 },
  { text: '│ OSI layer:   3 (Network)', cls: 't-label', pause: 30 },
  { text: '│ Confidence:  HIGH (Evidence quoted: MTU 1500 vs MTU 1400)', cls: 't-val', pause: 30 },
  { text: '│ Next cmd:    show ip ospf neighbor GigabitEthernet0/0', cls: 't-cmd', pause: 30 },
  { text: '│ Fix command: interface Gi0/0 -> ip mtu 1500', cls: 't-green', pause: 40 },
  { text: '└───────────────────────────────────────────────────────────────', cls: 't-border', pause: 120 },
  { text: '', pause: 40 },
  { type: 'review' }
];

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function runTrace(container) {
  container.innerHTML = '';

  for (const line of traceLines) {
    if (line.type === 'review') {
      await addReviewSection(container);
      continue;
    }

    const el = document.createElement('div');
    if (line.cls) el.className = line.cls;
    container.appendChild(el);

    if (reducedMotion) {
      el.textContent = line.text;
      container.scrollTop = container.scrollHeight;
      continue;
    }

    for (let i = 0; i < line.text.length; i++) {
      el.textContent += line.text[i];
      container.scrollTop = container.scrollHeight;
      await sleep(5);
    }

    await sleep(line.pause || 40);
  }
}

function addReviewSection(container) {
  return new Promise(resolve => {
    const prompt = document.createElement('div');
    prompt.className = 't-green';
    prompt.textContent = '▶ MANDATORY HUMAN REVIEW REQUIRED';
    container.appendChild(prompt);
    container.scrollTop = container.scrollHeight;

    const wait = reducedMotion ? 0 : 150;
    setTimeout(() => {
      const row = document.createElement('div');
      row.style.marginTop = '6px';
      row.style.paddingBottom = '4px';

      ['ACCEPT', 'EDIT', 'REJECT'].forEach(label => {
        const btn = document.createElement('button');
        btn.className = 'rv-btn';
        btn.textContent = label;
        btn.dataset.action = label.toLowerCase();
        btn.addEventListener('click', handleReview);
        row.appendChild(btn);
      });

      container.appendChild(row);
      container.scrollTop = container.scrollHeight;
      resolve();
    }, wait);
  });
}

function handleReview(e) {
  const action = e.target.dataset.action;
  const row = e.target.parentElement;
  const container = row.closest('.terminal-body');

  row.querySelectorAll('.rv-btn').forEach(b => {
    b.disabled = true;
    b.style.pointerEvents = 'none';
    b.style.opacity = '0.35';
  });

  e.target.style.opacity = '1';
  if (action === 'accept') e.target.classList.add('is-accept');
  else if (action === 'reject') e.target.classList.add('is-reject');
  else e.target.classList.add('is-edit');

  const result = document.createElement('div');
  result.style.marginTop = '8px';

  if (action === 'accept') {
    result.className = 't-green';
    result.textContent = '✓ Diagnosis accepted — recorded in review/review_log.csv (Accepted)';
  } else if (action === 'reject') {
    result.className = 't-red';
    result.textContent = '✗ Diagnosis rejected — recorded in review/review_log.csv (Rejected)';
  } else {
    result.className = 't-amber';
    result.textContent = '> Correction added to review/review_log.csv (Edited): ';
    const cursor = document.createElement('span');
    cursor.className = 't-cursor';
    result.appendChild(cursor);
  }

  container.appendChild(result);

  const replayWrap = document.createElement('div');
  replayWrap.style.marginTop = '12px';
  const replayBtn = document.createElement('button');
  replayBtn.className = 'replay-link';
  replayBtn.textContent = 'replay trace';
  replayBtn.addEventListener('click', () => runTrace(container));
  replayWrap.appendChild(replayBtn);
  container.appendChild(replayWrap);

  container.scrollTop = container.scrollHeight;
}

/* ── Charts Initialization ── */
let chartInstances = {};

function initCharts() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#8B949E' : '#5C6370';
  const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)';

  // Chart 1: Verdicts
  const ctxVerdicts = document.getElementById("chart-verdicts");
  if (ctxVerdicts) {
    if (chartInstances.verdicts) chartInstances.verdicts.destroy();
    chartInstances.verdicts = new Chart(ctxVerdicts.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: ["Accepted (71.9%)", "Edited (15.6%)", "Rejected (12.5%)"],
        datasets: [{
          data: [23, 5, 4],
          backgroundColor: ["#3DDC97", "#FFB454", "#FF5C5C"],
          borderColor: isDark ? "#131A21" : "#FFFFFF",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { color: textColor, font: { family: "JetBrains Mono", size: 11 } } }
        }
      }
    });
  }

  // Chart 2: Tag Distribution
  const ctxTags = document.getElementById("chart-tags");
  if (ctxTags) {
    if (chartInstances.tags) chartInstances.tags.destroy();
    chartInstances.tags = new Chart(ctxTags.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: ["Routing (7)", "Wireless/L2 (6)", "DHCP (5)", "NAT (4)", "ACL (4)", "VLAN (3)", "DNS (3)"],
        datasets: [{
          data: [7, 6, 5, 4, 4, 3, 3],
          backgroundColor: ["#79C0FF", "#D2A8FF", "#3DDC97", "#FFB454", "#56D4DD", "#FFA657", "#FF7B72"],
          borderColor: isDark ? "#131A21" : "#FFFFFF",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { color: textColor, font: { family: "JetBrains Mono", size: 10 } } }
        }
      }
    });
  }

  // Chart 3: Layers Bar
  const ctxLayers = document.getElementById("chart-layers");
  if (ctxLayers) {
    if (chartInstances.layers) chartInstances.layers.destroy();
    chartInstances.layers = new Chart(ctxLayers.getContext("2d"), {
      type: "bar",
      data: {
        labels: ["Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 7"],
        datasets: [{
          data: [1, 9, 13, 3, 6],
          backgroundColor: "#79C0FF",
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { grid: { color: gridColor }, ticks: { color: textColor, font: { family: "JetBrains Mono" } } },
          x: { grid: { display: false }, ticks: { color: textColor, font: { family: "JetBrains Mono" } } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // Chart 4: Failure by Domain
  const ctxFailures = document.getElementById("chart-failures");
  if (ctxFailures) {
    if (chartInstances.failures) chartInstances.failures.destroy();
    chartInstances.failures = new Chart(ctxFailures.getContext("2d"), {
      type: "bar",
      data: {
        labels: ["NAT", "DHCP", "DNS", "Routing", "ACL", "Wireless/L2"],
        datasets: [{
          data: [2, 2, 2, 1, 1, 1],
          backgroundColor: "#FFB454",
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: textColor, stepSize: 1, font: { family: "JetBrains Mono" } } },
          y: { grid: { display: false }, ticks: { color: textColor, font: { family: "JetBrains Mono" } } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }
}

/* ── Render Cases Table ── */
function renderTable(cases) {
  const tbody = document.getElementById("cases-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (cases.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:30px; color:var(--fg-muted);">No cases match the selected filters.</td></tr>`;
    return;
  }

  cases.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong style="color:var(--blue);">${c.case_id}</strong></td>
      <td><span class="tag-badge">${c.tag}</span></td>
      <td><span>L${c.layer}</span></td>
      <td><span class="tag-badge" style="color:${c.severity==='High'?'var(--red)':c.severity==='Medium'?'var(--amber)':'var(--green)'}">${c.severity}</span></td>
      <td style="max-width:320px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${c.symptom}">${c.symptom}</td>
      <td><span class="tag-badge" style="color:${c.rule_verdict==='FLAGGED'?'var(--amber)':'var(--fg-muted)'}">${c.rule_verdict}</span></td>
      <td><span style="text-transform:capitalize; font-weight:600; color:${c.ai_conf==='high'?'var(--green)':c.ai_conf==='medium'?'var(--amber)':'var(--red)'}">${c.ai_conf}</span></td>
      <td><span class="verdict-tag ${c.human_verdict}">${c.human_verdict}</span></td>
      <td><button class="btn-inspect-mini" onclick="openCaseModal('${c.case_id}')">Inspect</button></td>
    `;
    tr.addEventListener("click", (e) => {
      if (e.target.tagName !== "BUTTON") {
        openCaseModal(c.case_id);
      }
    });
    tbody.appendChild(tr);
  });
}

function applyFilters() {
  const searchVal = document.getElementById("filter-search").value.toLowerCase();
  const tagVal = document.getElementById("filter-tag").value;
  const verdictVal = document.getElementById("filter-verdict").value;
  const sevVal = document.getElementById("filter-severity").value;

  const filtered = DATASET.filter(c => {
    const matchesSearch = 
      c.case_id.toLowerCase().includes(searchVal) ||
      c.symptom.toLowerCase().includes(searchVal) ||
      c.expected_fault.toLowerCase().includes(searchVal) ||
      c.tag.toLowerCase().includes(searchVal);

    const matchesTag = tagVal === "ALL" || c.tag === tagVal;
    const matchesVerdict = verdictVal === "ALL" || c.human_verdict === verdictVal;
    const matchesSev = sevVal === "ALL" || c.severity === sevVal;

    return matchesSearch && matchesTag && matchesVerdict && matchesSev;
  });

  renderTable(filtered);
}

/* ── Render Responsible AI Cards ── */
function renderRAICards() {
  const container = document.getElementById("rai-container");
  if (!container) return;
  container.innerHTML = "";

  RAI_CASES.forEach(r => {
    const card = document.createElement("div");
    card.className = "p-5 rounded border";
    card.style.background = "var(--surface)";
    card.style.borderColor = "var(--border)";
    card.innerHTML = `
      <div class="flex justify-between items-center mb-3">
        <div class="flex items-center gap-2">
          <span class="font-mono text-xs px-2 py-0.5 rounded font-bold" style="background:var(--blue); color:#000">${r.case_id}</span>
          <h3 class="font-mono text-sm font-bold" style="color:var(--fg)">${r.title}</h3>
        </div>
        <span class="tag-badge">${r.domain}</span>
      </div>

      <div class="sec-label mt-3">AI Initial Misdiagnosis / Hallucination:</div>
      <div class="font-mono text-xs p-2.5 rounded mb-2" style="background:var(--surface-2); border-left:3px solid var(--red); color:var(--red)">${r.ai_said}</div>

      <div class="sec-label mt-3">Ground Truth Verified by Human Reviewer:</div>
      <div class="font-mono text-xs p-2.5 rounded mb-2" style="background:var(--surface-2); border-left:3px solid var(--green); color:var(--green)">${r.ground_truth}</div>

      <div class="sec-label mt-3">Root Cause Analysis of AI Failure:</div>
      <div class="font-sans text-xs p-2.5 rounded mb-2" style="background:var(--surface-2); color:var(--fg-muted)">${r.why_failed}</div>

      <div class="sec-label mt-3">Engineering Safeguard Implemented:</div>
      <div class="font-mono text-xs p-2.5 rounded" style="background:var(--surface-2); border-left:3px solid var(--blue); color:var(--blue)">${r.safeguard}</div>
    `;
    container.appendChild(card);
  });
}

/* ── Modal Diff Inspector ── */
window.openCaseModal = function(caseId) {
  const c = DATASET.find(x => x.case_id === caseId);
  if (!c) return;

  document.getElementById("modal-case-id").innerText = c.case_id;
  document.getElementById("modal-title").innerText = c.symptom;

  document.getElementById("modal-tag").innerText = c.tag;
  document.getElementById("modal-layer").innerText = `Layer ${c.layer}`;
  document.getElementById("modal-severity").innerText = `${c.severity} Severity`;
  document.getElementById("modal-verdict").innerText = `Verdict: ${c.human_verdict}`;
  document.getElementById("modal-verdict").className = `verdict-tag ${c.human_verdict}`;

  document.getElementById("modal-evidence-text").innerText = c.show_output;
  document.getElementById("modal-rule-finding").innerText = c.rule_finding;
  document.getElementById("modal-ground-truth").innerText = c.expected_fault;

  document.getElementById("modal-ai-conf").innerText = c.ai_conf.toUpperCase();
  document.getElementById("modal-ai-conf").style.color = c.ai_conf === 'high' ? 'var(--green)' : c.ai_conf === 'medium' ? 'var(--amber)' : 'var(--red)';
  document.getElementById("modal-ai-cause").innerText = c.ai_cause;
  document.getElementById("modal-ai-evidence").innerText = c.ai_evidence;

  const fixList = document.getElementById("modal-ai-fix");
  fixList.innerHTML = "";
  c.ai_fix.forEach(step => {
    const li = document.createElement("li");
    li.innerText = step;
    fixList.appendChild(li);
  });

  const verdictBanner = document.getElementById("modal-verdict-banner");
  verdictBanner.className = `verdict-tag ${c.human_verdict} w-full text-center py-2`;
  verdictBanner.innerText = `HUMAN REVIEW DECISION: ${c.human_verdict.toUpperCase()}`;

  document.getElementById("modal-reviewer-notes").innerText = c.reviewer_notes;
  document.getElementById("modal-human-edits").innerText = c.human_edits;

  document.getElementById("case-modal").classList.remove("hidden");
};

function closeModal() {
  document.getElementById("case-modal").classList.add("hidden");
}

/* ── DOM Init ── */
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  renderTable(DATASET);
  renderRAICards();

  // Terminal observer
  const terminalBody = document.getElementById('terminal-body');
  if (terminalBody) {
    let traceStarted = false;
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && !traceStarted) {
        traceStarted = true;
        setTimeout(() => runTrace(terminalBody), 400);
      }
    }, { threshold: 0.15 });
    observer.observe(terminalBody);
  }

  // Navigation Tabs switching
  document.querySelectorAll(".nav-tab-btn").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab-btn").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content-pane").forEach(p => p.classList.remove("active"));

      const targetId = tab.getAttribute("data-target");
      document.querySelectorAll(`[data-target="${targetId}"]`).forEach(t => t.classList.add("active"));
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Search & Filter listeners
  const searchInput = document.getElementById("filter-search");
  if (searchInput) searchInput.addEventListener("input", applyFilters);

  const tagFilter = document.getElementById("filter-tag");
  if (tagFilter) tagFilter.addEventListener("change", applyFilters);

  const verdictFilter = document.getElementById("filter-verdict");
  if (verdictFilter) verdictFilter.addEventListener("change", applyFilters);

  const sevFilter = document.getElementById("filter-severity");
  if (sevFilter) sevFilter.addEventListener("change", applyFilters);

  // Modal close handlers
  const modalCloseBtn = document.getElementById("modal-close");
  if (modalCloseBtn) modalCloseBtn.addEventListener("click", closeModal);

  const modalBackdrop = document.getElementById("case-modal");
  if (modalBackdrop) {
    modalBackdrop.addEventListener("click", (e) => {
      if (e.target.id === "case-modal") closeModal();
    });
  }

  // Theme Toggle
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const html = document.documentElement;
      const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      themeToggle.textContent = next === 'dark' ? 'light' : 'dark';
      themeToggle.setAttribute('aria-label',
        next === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
      );
      // Re-render charts with updated theme colors
      initCharts();
    });
  }
});
