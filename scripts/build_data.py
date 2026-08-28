"""
NetSage AI - Synthetic Benchmark Dataset & CLI Evidence Generator
Generates 32 synthetically modeled, internally consistent Cisco networking cases and CLI evidence files.
Validated for topology, IP addressing, subnet mask, and VLAN coherence.
"""
import os
import csv
import json

BASE_DIR = r"c:\Users\Sanjay\Documents\antigravity\ciscovip"
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw_evidence")

os.makedirs(RAW_DIR, exist_ok=True)

CASES = [
    {
        "case_id": "CASE-001",
        "symptom": "Broadcast traffic leaking and CDP error logs between Distribution Switch A and Switch B across trunk link Gi0/1.",
        "topology_note": "Dist-SW1 (Gi0/1, Native VLAN 10) connected to Dist-SW2 (Gi0/1, Native VLAN 20) via 802.1Q trunk. VLAN 10 is Sales (192.168.10.0/24) and VLAN 20 is HR (192.168.20.0/24).",
        "show_output": """Dist-SW1# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      10

Port        Vlans allowed on trunk
Gi0/1       1-4094

Port        Vlans allowed and active in management domain
Gi0/1       1,10,20,30

Dist-SW1# show log | include %CDP-4-NATIVE_VLAN_MISMATCH
%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (10), with Dist-SW2 GigabitEthernet0/1 (20).

Dist-SW2# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      20""",
        "expected_fault": "Native VLAN mismatch on 802.1Q trunk link Gi0/1 (Dist-SW1 has native VLAN 10, Dist-SW2 has native VLAN 20).",
        "osi_layer": 2,
        "concept_tag": "VLAN",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_001_show_output.txt"
    },
    {
        "case_id": "CASE-002",
        "symptom": "New workstations connected to Access-SW1 port Gi0/5 cannot communicate or get link status on Engineering VLAN 50.",
        "topology_note": "Access-SW1 port Gi0/5 is configured as an access port in VLAN 50 (192.168.50.0/24) for Engineering department.",
        "show_output": """Access-SW1# show interfaces GigabitEthernet0/5 switchport
Name: Gi0/5
Switchport: Enabled
Administrative Mode: static access
Operational Mode: static access
Administrative Trunking Encapsulation: negotiate
Negotiation of Trunking: Off
Access Mode VLAN: 50 (Inactive)
Trunking Native Mode VLAN: 1 (default)

Access-SW1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Gi0/1, Gi0/2, Gi0/3, Gi0/4
10   Sales                            active    Gi0/6, Gi0/7
20   HR                               active    Gi0/8, Gi0/9
30   Management                       active    Gi0/10""",
        "expected_fault": "Access port Gi0/5 is assigned to VLAN 50, but VLAN 50 does not exist in the switch VLAN database (vlan.dat), marking port Inactive.",
        "osi_layer": 2,
        "concept_tag": "VLAN",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_002_show_output.txt"
    },
    {
        "case_id": "CASE-003",
        "symptom": "IP phones in Voice VLAN 40 cannot reach the Call Manager server through the core switch link.",
        "topology_note": "Access-SW2 uplink Gi0/24 connects to Core-SW1. Voice traffic is in VLAN 40 (10.40.0.0/24), Data traffic in VLAN 10.",
        "show_output": """Access-SW2# show interfaces Gi0/24 trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/24      on               802.1q         trunking      1

Port        Vlans allowed on trunk
Gi0/24      10,20,30

Port        Vlans in spanning tree forwarding state and not pruned
Gi0/24      10,20,30

Access-SW2# show run interface Gi0/24
interface GigabitEthernet0/24
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30""",
        "expected_fault": "VLAN 40 (Voice) is pruned from the trunk allowed list on interface Gi0/24 (only 10,20,30 allowed).",
        "osi_layer": 2,
        "concept_tag": "VLAN",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_003_show_output.txt"
    },
    {
        "case_id": "CASE-004",
        "symptom": "Finance PC connected to Access Switch port Gi0/12 suddenly lost all network connectivity. Interface indicator is amber.",
        "topology_note": "Port Gi0/12 on Acc-SW3 configured with Spanning Tree PortFast and BPDU Guard enabled for edge end-host access.",
        "show_output": """Acc-SW3# show interfaces GigabitEthernet0/12 status
Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/12    Finance_PC_12      err-disabled 10           auto   auto 10/100/1000BaseTX

Acc-SW3# show log | include %SPANTREE-2-BLOCK_BPDUGUARD
%SPANTREE-2-BLOCK_BPDUGUARD: Received BPDU on port Gi0/12 with BPDU Guard enabled. Disabling port.
%PM-4-ERR_DISABLE: bpduguard error detected on Gi0/12, putting Gi0/12 in err-disable state

Acc-SW3# show run interface Gi0/12
interface GigabitEthernet0/12
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 spanning-tree bpduguard enable""",
        "expected_fault": "Port Gi0/12 was placed into err-disabled state by STP BPDU Guard after receiving unauthorized BPDU packets from an unmanaged switch.",
        "osi_layer": 2,
        "concept_tag": "Wireless/L2",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_004_show_output.txt"
    },
    {
        "case_id": "CASE-005",
        "symptom": "Production Web Server SRV-01 (192.168.10.50) can reach hosts in its lower IP range but cannot reach the default gateway 192.168.10.1.",
        "topology_note": "LAN Subnet is 192.168.10.0/24. Router Gateway is 192.168.10.1/24. SRV-01 is statically assigned IP 192.168.10.50.",
        "show_output": """SRV-01# ipconfig /all
Ethernet adapter Local Area Connection:
   IPv4 Address. . . . . . . . . . . : 192.168.10.50
   Subnet Mask . . . . . . . . . . . : 255.255.255.240
   Default Gateway . . . . . . . . . : 192.168.10.1

Core-RTR# show ip interface GigabitEthernet0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet address is 192.168.10.1/24
  Broadcast address is 192.168.10.255
  Address determined by setup command
  MTU is 1500 bytes""",
        "expected_fault": "Subnet mask mismatch on server SRV-01: configured with /28 (255.255.255.240, valid range 192.168.10.48-63) making gateway 192.168.10.1 appear off-subnet.",
        "osi_layer": 3,
        "concept_tag": "Routing",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_005_show_output.txt"
    },
    {
        "case_id": "CASE-006",
        "symptom": "Database Server DB-01 cannot communicate with external API endpoints or other subnets.",
        "topology_note": "DB-01 resides on VLAN 20 (10.10.20.0/24). Core Router SVI Vlan20 is 10.10.20.1/24 and Vlan30 is 10.10.30.1/24.",
        "show_output": """DB-01# ifconfig eth0
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.10.20.15  netmask 255.255.255.0  broadcast 10.10.20.255

DB-01# ip route show
default via 10.10.30.1 dev eth0
10.10.20.0/24 dev eth0 proto kernel scope link src 10.10.20.15

Core-RTR# show ip interface brief | include Vlan
Vlan20                 10.10.20.1      YES manual up                    up
Vlan30                 10.10.30.1      YES manual up                    up""",
        "expected_fault": "Default gateway mismatch on DB-01: configured with 10.10.30.1 (VLAN 30 gateway) instead of 10.10.20.1 (local subnet gateway).",
        "osi_layer": 3,
        "concept_tag": "Routing",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_006_show_output.txt"
    },
    {
        "case_id": "CASE-007",
        "symptom": "OSPF neighbor adjacency between Core-R1 and Dist-R2 is stuck in EXSTART/EXCHANGE state; routing updates are not exchanged.",
        "topology_note": "Core-R1 (Gi0/0, 10.0.0.1/30) connects to Dist-R2 (Gi0/0, 10.0.0.2/30) in OSPF Area 0.",
        "show_output": """Core-R1# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
192.168.2.2       1   EXSTART/  -     00:00:33    10.0.0.2        GigabitEthernet0/0

Core-R1# show ip interface GigabitEthernet0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet address is 10.0.0.1/30
  Broadcast address is 255.255.255.255
  Address determined by setup command
  MTU is 1500 bytes

Dist-R2# show ip interface GigabitEthernet0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet address is 10.0.0.2/30
  Broadcast address is 255.255.255.255
  Address determined by setup command
  MTU is 1400 bytes

Dist-R2# show log | include %OSPF-5-ADJCHG
%OSPF-5-ADJCHG: Process 1, Nbr 192.168.1.1 on GigabitEthernet0/0 from LOADING to EXSTART, Seq Number Mismatch""",
        "expected_fault": "OSPF interface MTU mismatch on link Gi0/0 (Core-R1 MTU 1500 vs Dist-R2 MTU 1400), causing DBD packet exchange failure and EXSTART hang.",
        "osi_layer": 3,
        "concept_tag": "Routing",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_007_show_output.txt"
    },
    {
        "case_id": "CASE-008",
        "symptom": "Branch office users can ping local servers but cannot access any public Internet websites (e.g. 8.8.8.8).",
        "topology_note": "Branch-RTR Gi0/1 (192.168.1.1/24 LAN) and Gi0/0 (203.0.113.2/30 WAN) connects to ISP Gateway 203.0.113.1.",
        "show_output": """Branch-RTR# show ip route
Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area

Gateway of last resort is not set

      192.168.1.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.1.0/24 is directly connected, GigabitEthernet0/1
L        192.168.1.1/32 is directly connected, GigabitEthernet0/1
      203.0.113.0/30 is variably subnetted, 2 subnets, 2 masks
C        203.0.113.0/30 is directly connected, GigabitEthernet0/0
L        203.0.113.2/32 is directly connected, GigabitEthernet0/0

Branch-RTR# ping 8.8.8.8
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 8.8.8.8, timeout is 2 seconds:
.....
Success rate is 0 percent (0/5)""",
        "expected_fault": "Missing default route (0.0.0.0/0) pointing to ISP Gateway 203.0.113.1 on Branch-RTR; Gateway of last resort is not set.",
        "osi_layer": 3,
        "concept_tag": "Routing",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_008_show_output.txt"
    },
    {
        "case_id": "CASE-009",
        "symptom": "Router HQ-RTR1 cannot form OSPF adjacency with Core-RTR2 across point-to-point link Gi0/2.",
        "topology_note": "HQ-RTR1 (172.16.1.1/30) and Core-RTR2 (172.16.1.2/30) are connected via Gi0/2 in OSPF Area 0.",
        "show_output": """HQ-RTR1# show ip ospf interface GigabitEthernet0/2
GigabitEthernet0/2 is up, line protocol is up
  Internet Address 172.16.1.1/30, Area 0, Attached via Interface Enable
  Process ID 1, Router ID 1.1.1.1, Network Type BROADCAST, Cost: 1
  No Hellos (Passive interface)

HQ-RTR1# show run | section router ospf
router ospf 1
 router-id 1.1.1.1
 passive-interface GigabitEthernet0/2
 network 172.16.1.0 0.0.0.3 area 0""",
        "expected_fault": "Interface GigabitEthernet0/2 is mistakenly configured as a passive-interface under OSPF process 1, suppressing Hello packets.",
        "osi_layer": 3,
        "concept_tag": "Routing",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_009_show_output.txt"
    },
    {
        "case_id": "CASE-010",
        "symptom": "BGP peering between Enterprise Edge router and ISP Border Router remains in Active/Idle state.",
        "topology_note": "Edge-RTR is in AS 65001. ISP Border Router is in AS 65500 with peering IP 198.51.100.1.",
        "show_output": """Edge-RTR# show ip bgp summary
BGP router identifier 10.0.0.1, local AS number 65001
BGP table version is 1, main routing table version 1

Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
198.51.100.1    4        65510       0       0        1    0    0 00:14:22 Active

Edge-RTR# show run | section router bgp
router bgp 65001
 bgp log-neighbor-changes
 neighbor 198.51.100.1 remote-as 65510

ISP-RTR# show run | section router bgp
router bgp 65500
 neighbor 198.51.100.2 remote-as 65001""",
        "expected_fault": "BGP Autonomous System (AS) number mismatch: Edge-RTR configured neighbor 198.51.100.1 with remote-as 65510 instead of ISP AS 65500.",
        "osi_layer": 3,
        "concept_tag": "Routing",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_010_show_output.txt"
    },
    {
        "case_id": "CASE-011",
        "symptom": "Static route to remote subnet 172.20.0.0/16 is not present in the routing table despite being in the running configuration.",
        "topology_note": "Edge-RTR configured with static route to 172.20.0.0/16 via next-hop IP 10.254.1.1.",
        "show_output": """Edge-RTR# show run | include ip route
ip route 172.20.0.0 255.255.0.0 10.254.1.1

Edge-RTR# show ip route 10.254.1.1
% Network not in table

Edge-RTR# show ip route 172.20.0.0
% Network not in table

Edge-RTR# show ip interface brief
Interface                  IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0         192.168.1.1     YES NVRAM  up                    up
GigabitEthernet0/1         10.100.1.1      YES NVRAM  up                    up""",
        "expected_fault": "Next-hop IP 10.254.1.1 is unreachable and has no matching entry in the routing table (recursive lookup failure), preventing static route installation.",
        "osi_layer": 3,
        "concept_tag": "Routing",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_011_show_output.txt"
    },
    {
        "case_id": "CASE-012",
        "symptom": "Internal clients in subnet 192.168.1.0/24 cannot access Internet servers. NAT translations table is completely empty.",
        "topology_note": "Gateway Router with LAN on Gi0/0 (192.168.1.1) and WAN on Gi0/1 (203.0.113.2) using NAT Overload.",
        "show_output": """GW-RTR# show run interface GigabitEthernet0/0
interface GigabitEthernet0/0
 description LAN Interface
 ip address 192.168.1.1 255.255.255.0
 ip nat outside

GW-RTR# show run interface GigabitEthernet0/1
interface GigabitEthernet0/1
 description WAN Interface to ISP
 ip address 203.0.113.2 255.255.255.252
 ip nat inside

GW-RTR# show ip nat translations
(empty)

GW-RTR# show run | include ip nat inside source
ip nat inside source list 1 interface GigabitEthernet0/1 overload""",
        "expected_fault": "NAT inside/outside interface statements are inverted: LAN interface Gi0/0 is configured with 'ip nat outside' and WAN interface Gi0/1 with 'ip nat inside'.",
        "osi_layer": 3,
        "concept_tag": "NAT",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_012_show_output.txt"
    },
    {
        "case_id": "CASE-013",
        "symptom": "Branch office PCs in subnet 192.168.20.0/24 cannot reach the Internet; NAT stats show 0 translation matches.",
        "topology_note": "Branch router NAT overload configured with access-list 10 permitting internal traffic for translation out Gi0/1.",
        "show_output": """Branch-RTR# show run | include ip nat
ip nat inside source list 10 interface GigabitEthernet0/1 overload

Branch-RTR# show access-lists 10
Standard IP access list 10
    10 permit 192.168.10.0, wildcard bits 0.0.0.255 (0 matches)

Branch-RTR# show ip interface GigabitEthernet0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet address is 192.168.20.1/24

Branch-RTR# show ip nat statistics
Total active translations: 0 (0 static, 0 dynamic; 0 extended)
Outside interfaces: GigabitEthernet0/1
Inside interfaces: GigabitEthernet0/0
Hits: 0  Misses: 142""",
        "expected_fault": "NAT ACL 10 permits 192.168.10.0/24 instead of the actual local LAN subnet 192.168.20.0/24, causing all client packets to miss the NAT rule.",
        "osi_layer": 3,
        "concept_tag": "NAT",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_013_show_output.txt"
    },
    {
        "case_id": "CASE-014",
        "symptom": "Outbound Internet connections drop intermittently; ISP router complains of ARP IP conflicts for 198.51.100.1.",
        "topology_note": "Edge Router NAT pool configured with public range. ISP default gateway interface is 198.51.100.1/29.",
        "show_output": """Edge-RTR# show run | section ip nat pool
ip nat pool CORP_POOL 198.51.100.1 198.51.100.6 netmask 255.255.255.248
ip nat inside source list 1 pool CORP_POOL overload

Edge-RTR# show ip interface GigabitEthernet0/1
GigabitEthernet0/1 is up, line protocol is up
  Internet address is 198.51.100.2/29

Edge-RTR# show ip route 0.0.0.0
Routing entry for 0.0.0.0/0, supernet
  Known via "static", distance 1, metric 0, candidate default path
  * 198.51.100.1""",
        "expected_fault": "Dynamic NAT pool CORP_POOL includes 198.51.100.1, which is the upstream ISP default gateway IP address, causing an IP conflict and ARP hijack.",
        "osi_layer": 3,
        "concept_tag": "NAT",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_014_show_output.txt"
    },
    {
        "case_id": "CASE-015",
        "symptom": "External customers cannot connect to public DMZ HTTPS server; DNS resolves to 203.0.113.205 but SYN packets are unanswered.",
        "topology_note": "Internal DMZ Server is 192.168.100.10. Public static IP allocated by ISP is 203.0.113.205.",
        "show_output": """Edge-GW# show run | include ip nat inside source static
ip nat inside source static 192.168.100.10 203.0.113.250

Edge-GW# show ip nat translations
Pro Inside global         Inside local          Outside local         Outside global
--- 203.0.113.250         192.168.100.10        ---                   ---

External-Client# nslookup secure.example.com
Server:  8.8.8.8
Address: 8.8.8.8#53

Non-authoritative answer:
Name:    secure.example.com
Address: 203.0.113.205""",
        "expected_fault": "Static 1-to-1 NAT IP configuration typo: mapped inside server to 203.0.113.250 instead of registered public DNS IP 203.0.113.205.",
        "osi_layer": 3,
        "concept_tag": "NAT",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_015_show_output.txt"
    },
    {
        "case_id": "CASE-016",
        "symptom": "Workstations on Sales VLAN 20 are unable to obtain IP addresses and fall back to APIPA (169.254.x.x).",
        "topology_note": "Clients reside in VLAN 20 (192.168.20.0/24). Central DHCP Server is located in Management VLAN 10 at 10.1.1.50.",
        "show_output": """Core-SW1# show run interface Vlan20
interface Vlan20
 description Sales_Department
 ip address 192.168.20.1 255.255.255.0
 no ip redirects

Core-SW1# show run interface Vlan10
interface Vlan10
 description Management_Servers
 ip address 10.1.1.1 255.255.255.0

Client-PC# ipconfig /renew
An error occurred while renewing interface Ethernet0 : unable to contact your DHCP server.""",
        "expected_fault": "Missing 'ip helper-address 10.1.1.50' under interface Vlan20 on Core-SW1 to forward client DHCP broadcast discovers to the central DHCP server.",
        "osi_layer": 7,
        "concept_tag": "DHCP",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_016_show_output.txt"
    },
    {
        "case_id": "CASE-017",
        "symptom": "Guests in conference room cannot connect to Guest Wi-Fi; DHCP discovery requests receive no offers.",
        "topology_note": "Local Router provides DHCP service for Guest subnet 192.168.100.0/24 with scope 192.168.100.100 to 192.168.100.150 (51 IPs).",
        "show_output": """Guest-RTR# show ip dhcp pool GUEST_WIFI
Pool GUEST_WIFI :
 Utilization mark (high/low)    : 100 / 0
 Subnet size (total/usable)     : 254/51
 Total addresses                : 51
 Leased addresses               : 51
 Excluded addresses             : 203
 Pending event                  : none

Guest-RTR# show ip dhcp conflict
IP address        Detection method   Detection time

Guest-RTR# show log | include %DHCPD-4-DECLINE
%DHCPD-4-DECLINE: Address pool GUEST_WIFI is full, cannot allocate address for client a483.e710.22aa""",
        "expected_fault": "DHCP address pool GUEST_WIFI is completely exhausted (51/51 leased addresses), rejecting new guest client lease requests.",
        "osi_layer": 7,
        "concept_tag": "DHCP",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_017_show_output.txt"
    },
    {
        "case_id": "CASE-018",
        "symptom": "Multiple employee laptops suddenly received default gateway 192.168.88.1 and lost access to corporate intranet resources.",
        "topology_note": "Corporate VLAN 10 is 10.10.10.0/24. Access-SW1 connects end-user desks on Gi0/1-24.",
        "show_output": """Employee-PC# ipconfig /all
   IPv4 Address. . . . . . . . . . . : 192.168.88.105
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.88.1
   DHCP Server . . . . . . . . . . . : 192.168.88.1

Access-SW1# show ip dhcp snooping
Switch DHCP snooping is disabled

Access-SW1# show mac address-table dynamic interface Gi0/8
          Mac Address Table
-------------------------------------------
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
10      00e0.4c68.1122    DYNAMIC     Gi0/8""",
        "expected_fault": "Rogue DHCP server connected to switch port Gi0/8 distributing rogue leases (192.168.88.0/24) because DHCP Snooping is disabled.",
        "osi_layer": 7,
        "concept_tag": "DHCP",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_018_show_output.txt"
    },
    {
        "case_id": "CASE-019",
        "symptom": "Network printer and Executive PC experience intermittent connection drops; switch console logs duplicate IP warnings.",
        "topology_note": "Subnet 192.168.1.0/24. Network Printer has static IP 192.168.1.25. DHCP server pool covers 192.168.1.1 to 192.168.1.100.",
        "show_output": """Core-RTR# show log | include %IP-4-DUPADDR
%IP-4-DUPADDR: Duplicate address 192.168.1.25 on GigabitEthernet0/0, sourced by 50eb.7112.44bb (PC) and 0011.2233.4455 (Printer)

Core-RTR# show ip dhcp binding | include 192.168.1.25
192.168.1.25        0150.eb71.1244.bb       Feb 28 2026 10:14 AM    Automatic

Core-RTR# show run | include ip dhcp excluded-address
ip dhcp excluded-address 192.168.1.1 192.168.1.10""",
        "expected_fault": "Duplicate IP address conflict: static printer IP 192.168.1.25 was not included in 'ip dhcp excluded-address' range and was leased to a dynamic host.",
        "osi_layer": 3,
        "concept_tag": "DHCP",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_019_show_output.txt"
    },
    {
        "case_id": "CASE-020",
        "symptom": "Default gateway 10.50.0.254 becomes unresponsive periodically; host ARP table points to a random workstation MAC address.",
        "topology_note": "VLAN 50 Subnet 10.50.0.0/24. Router Gateway is 10.50.0.254.",
        "show_output": """Core-SW# show run | section ip dhcp
ip dhcp excluded-address 10.50.0.1 10.50.0.50
ip dhcp pool VLAN50_POOL
 network 10.50.0.0 255.255.255.0
 default-router 10.50.0.254
 dns-server 10.50.0.10

Core-SW# show ip dhcp binding | include 10.50.0.254
10.50.0.254         01cc.4477.8899.aa       Feb 28 2026 09:30 AM    Automatic""",
        "expected_fault": "Default gateway IP 10.50.0.254 was omitted from 'ip dhcp excluded-address' (which only excluded .1-.50), causing DHCP pool to lease the gateway IP to a host.",
        "osi_layer": 7,
        "concept_tag": "DHCP",
        "severity": "Low",
        "evidence_file": "data/raw_evidence/case_020_show_output.txt"
    },
    {
        "case_id": "CASE-021",
        "symptom": "Finance department hosts in 192.168.10.0/24 cannot reach internal Accounting SQL server at 192.168.30.50.",
        "topology_note": "Core Router interfaces Gi0/1 (VLAN 10: 192.168.10.1) and Gi0/3 (VLAN 30: 192.168.30.1).",
        "show_output": """Core-RTR# show access-lists 10
Standard IP access list 10
    10 deny   192.168.10.0, wildcard bits 0.0.0.255 (450 matches)
    20 permit any (1200 matches)

Core-RTR# show run interface GigabitEthernet0/3
interface GigabitEthernet0/3
 description Accounting VLAN 30 Interface
 ip address 192.168.30.1 255.255.255.0
 ip access-group 10 out""",
        "expected_fault": "Standard ACL 10 applied outbound on interface Gi0/3 explicitly denies source subnet 192.168.10.0/24 from reaching the Accounting subnet.",
        "osi_layer": 3,
        "concept_tag": "ACL",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_021_show_output.txt"
    },
    {
        "case_id": "CASE-022",
        "symptom": "Internal users can initiate TCP web connections to external web servers, but pages time out and TCP handshake never finishes.",
        "topology_note": "Edge Router with inbound ACL applied on WAN interface Gi0/1 facing ISP.",
        "show_output": """Edge-RTR# show access-lists INBOUND_FILTER
Extended IP access list INBOUND_FILTER
    10 permit udp any any eq domain
    20 permit icmp any any echo-reply
    30 deny ip any any (18934 matches)

Edge-RTR# show run interface GigabitEthernet0/1
interface GigabitEthernet0/1
 ip address 203.0.113.2 255.255.255.252
 ip access-group INBOUND_FILTER in""",
        "expected_fault": "Inbound ACL INBOUND_FILTER on WAN interface Gi0/1 is missing 'permit tcp any any established', blocking return SYN-ACK and ACK web traffic.",
        "osi_layer": 4,
        "concept_tag": "ACL",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_022_show_output.txt"
    },
    {
        "case_id": "CASE-023",
        "symptom": "Branch office cannot resolve external domain names (e.g., cisco.com); nslookup queries to public DNS 8.8.8.8 time out.",
        "topology_note": "Branch router interface Gi0/0 connects to ISP. Outbound traffic is inspected by ACL SEC_FILTER.",
        "show_output": """Branch-RTR# show access-lists SEC_FILTER
Extended IP access list SEC_FILTER
    10 permit tcp 192.168.1.0 0.0.0.255 any eq www
    20 permit tcp 192.168.1.0 0.0.0.255 any eq 443
    30 permit tcp 192.168.1.0 0.0.0.255 any eq domain
    40 deny ip any any (532 matches)

Branch-RTR# show run interface GigabitEthernet0/0
interface GigabitEthernet0/0
 ip access-group SEC_FILTER out""",
        "expected_fault": "ACL SEC_FILTER only permits TCP port 53 (eq domain) but denies UDP port 53 (standard DNS queries operate over UDP 53).",
        "osi_layer": 4,
        "concept_tag": "ACL",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_023_show_output.txt"
    },
    {
        "case_id": "CASE-024",
        "symptom": "Guest users in VLAN 90 are able to ping and browse internal corporate servers in VLAN 10 despite restrictive guest ACL.",
        "topology_note": "Guest subnet is VLAN 90 (172.16.90.0/24). Corporate LAN is VLAN 10 (172.16.10.0/24).",
        "show_output": """Core-SW# show access-lists BLOCK_GUEST
Extended IP access list BLOCK_GUEST
    10 deny ip 172.16.90.0 0.0.0.255 172.16.10.0 0.0.0.255
    20 permit ip 172.16.90.0 0.0.0.255 any

Core-SW# show run interface GigabitEthernet0/1
interface GigabitEthernet0/1
 description Uplink to WAN Router
 ip access-group BLOCK_GUEST out

Core-SW# show run interface Vlan90
interface Vlan90
 description Guest Gateway
 ip address 172.16.90.1 255.255.255.0""",
        "expected_fault": "ACL BLOCK_GUEST was applied outbound on WAN interface Gi0/1 instead of inbound on interface Vlan90, leaving inter-VLAN guest traffic uninspected.",
        "osi_layer": 3,
        "concept_tag": "ACL",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_024_show_output.txt"
    },
    {
        "case_id": "CASE-025",
        "symptom": "All domain workstation logins and internal portal accesses fail with 'Domain controller cannot be contacted' after server maintenance.",
        "topology_note": "Primary DNS Server 10.10.1.20 was decommissioned; new AD DNS server is 10.10.1.50.",
        "show_output": """Core-RTR# show run | section ip dhcp pool
ip dhcp pool CORP_USERS
 network 10.10.10.0 255.255.255.0
 default-router 10.10.10.1
 dns-server 10.10.1.20

Core-RTR# ping 10.10.1.20
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 10.10.1.20, timeout is 2 seconds:
.....
Success rate is 0 percent (0/5)

Core-RTR# ping 10.10.1.50
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 10.10.1.50, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5)""",
        "expected_fault": "DHCP pool CORP_USERS is configured with decommissioned DNS server IP 10.10.1.20 instead of the active DNS server 10.10.1.50.",
        "osi_layer": 7,
        "concept_tag": "DNS",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_025_show_output.txt"
    },
    {
        "case_id": "CASE-026",
        "symptom": "Branch office PCs cannot resolve internal intranet URLs (e.g. portal.corp.local) but public websites resolve normally.",
        "topology_note": "Branch DNS caching forwarder runs on Branch-GW (192.168.1.1). Corporate internal DNS server is 10.0.0.5.",
        "show_output": """Branch-GW# show run | include ip dns
ip dns server
ip dns forwarding
ip name-server 8.8.8.8
ip name-server 8.8.4.4

Branch-GW# show hosts
Default domain is corp.local
Name/address lookup uses domain service
Name servers are 8.8.8.8, 8.8.4.4""",
        "expected_fault": "Split-brain DNS misconfiguration: Branch-GW name-servers are set exclusively to public resolvers (8.8.8.8) with no conditional forwarder for internal zone 'corp.local' to 10.0.0.5.",
        "osi_layer": 7,
        "concept_tag": "DNS",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_026_show_output.txt"
    },
    {
        "case_id": "CASE-027",
        "symptom": "Workstations fail to resolve DNS records for domains utilizing DNSSEC (large UDP response payloads > 1400 bytes) across IPsec VPN.",
        "topology_note": "Site-to-Site IPsec VPN tunnel between Branch (Tunnel0, MTU 1400) and HQ.",
        "show_output": """Branch-RTR# show interfaces Tunnel0
Tunnel0 is up, line protocol is up
  Hardware is Tunnel
  Internet address is 10.255.0.2/30
  MTU 1400 bytes, BW 100000 Kbit/sec, DLY 50000 usec
  Tunnel source 203.0.113.2, destination 198.51.100.2
  Tunnel protocol/transport IPSEC/IP

Branch-RTR# show ip interface Tunnel0 | include MTU
  MTU is 1400 bytes
  ICMP unreachables are never sent

Branch-RTR# show run interface Tunnel0
interface Tunnel0
 ip address 10.255.0.2 255.255.255.252
 tunnel source GigabitEthernet0/0
 tunnel destination 198.51.100.2
 no ip unreachables""",
        "expected_fault": "Large UDP DNS responses exceed tunnel MTU 1400 with DF (Don't Fragment) bit set; 'no ip unreachables' suppresses ICMP Fragmentation Needed, creating a PMTU black hole.",
        "osi_layer": 4,
        "concept_tag": "DNS",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_027_show_output.txt"
    },
    {
        "case_id": "CASE-028",
        "symptom": "File transfers between File Server and clients are extremely sluggish with excessive packet drops and late collisions.",
        "topology_note": "File Server connected to Switch port Gi0/3. Server NIC is hardcoded to 100Mbps Full Duplex.",
        "show_output": """Switch-1# show interfaces GigabitEthernet0/3
GigabitEthernet0/3 is up, line protocol is up (connected)
  Hardware is Gigabit Ethernet, address is 0014.f25a.3303
  Auto-duplex, Auto-speed
  Half-duplex, 100Mb/s, media type is 10/100/1000BaseTX
  5829314 packets input, 492019482 bytes, 0 no buffer
  Received 28194 broadcasts, 0 runts, 0 giants, 0 throttles
  49102 input errors, 48920 CRC, 0 frame, 0 overrun, 0 ignored
  38192 late collision, 18290 deferred, 12 lost carrier""",
        "expected_fault": "Duplex mismatch on port Gi0/3: Switch auto-negotiated to Half-Duplex because server NIC was hardcoded to Full-Duplex without autonegotiation, causing late collisions and CRC errors.",
        "osi_layer": 1,
        "concept_tag": "Wireless/L2",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_028_show_output.txt"
    },
    {
        "case_id": "CASE-029",
        "symptom": "Conference room network jack suddenly stopped working when a second laptop was connected via a mini desk switch.",
        "topology_note": "Access switch port Gi0/7 has Cisco Port Security enabled for single MAC address.",
        "show_output": """Acc-SW1# show port-security interface GigabitEthernet0/7
Port Security              : Enabled
Port Status                : Secure-shutdown
Violation Mode             : Shutdown
Aging Time                 : 0 mins
Aging Type                 : Absolute
SecureStatic Address Aging : Disabled
Maximum MAC Addresses      : 1
Total MAC Addresses        : 1
Configured MAC Addresses   : 0
Sticky MAC Addresses       : 1
Last Source Address:Vlan   : 0025.90cd.e412:10
Security Violation Count   : 1

Acc-SW1# show interfaces GigabitEthernet0/7 status
Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/7     Conf_Room_Jack     err-disabled 10           auto   auto 10/100/1000BaseTX""",
        "expected_fault": "Port Security violation on Gi0/7: maximum MAC address limit of 1 was exceeded when second device connected, placing the port in err-disabled shutdown state.",
        "osi_layer": 2,
        "concept_tag": "Wireless/L2",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_029_show_output.txt"
    },
    {
        "case_id": "CASE-030",
        "symptom": "Users on Subnet 192.168.1.0/24 report MITM browser security warnings; traffic to the default gateway is being intercepted.",
        "topology_note": "Legitimate Default Gateway IP 192.168.1.1 MAC is 0000.0c07.ac01. Host 192.168.1.199 MAC is a483.e721.99aa.",
        "show_output": """Core-SW# show ip arp
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.1             -   0000.0c07.ac01  ARPA   Vlan1
Internet  192.168.1.199           2   a483.e721.99aa  ARPA   Vlan1

Host-PC# arp -a
Interface: 192.168.1.45 --- 0xb
  Internet Address      Physical Address      Type
  192.168.1.1           a483-e721-99aa        dynamic
  192.168.1.199         a483-e721-99aa        dynamic

Core-SW# show ip arp inspection
Source Mac Validation      : Disabled
Destination Mac Validation : Disabled
IP Address Validation      : Disabled
Vlan 1 DAI is disabled""",
        "expected_fault": "ARP Poisoning / Gateway MAC Spoofing attack: rogue host 192.168.1.199 (MAC a483.e721.99aa) poisoned host ARP tables because Dynamic ARP Inspection (DAI) is disabled.",
        "osi_layer": 2,
        "concept_tag": "Wireless/L2",
        "severity": "High",
        "evidence_file": "data/raw_evidence/case_030_show_output.txt"
    },
    {
        "case_id": "CASE-031",
        "symptom": "Uplink port Gi0/24 on Core-SW connecting to newly added Distribution Switch has entered blocking state.",
        "topology_note": "Core-SW is designated STP Root Bridge with Root Guard enabled on downstream ports. Dist-SW was booted with default STP priority 32768.",
        "show_output": """Core-SW# show spanning-tree inconsistentports
Name                 Interface              Inconsistency
-------------------- ---------------------- ------------------
VLAN0001             GigabitEthernet0/24    Root Inconsistent
VLAN0010             GigabitEthernet0/24    Root Inconsistent

Core-SW# show log | include %SPANTREE-2-ROOTGUARDBLOCK
%SPANTREE-2-ROOTGUARDBLOCK: Root Guard block port GigabitEthernet0/24 on VLAN0001.
%SPANTREE-2-ROOTGUARDBLOCK: Root Guard block port GigabitEthernet0/24 on VLAN0010.

Dist-SW# show spanning-tree
VLAN0001
  Spanning tree enabled protocol rstp
  Root ID    Priority    0
             Address     001b.d45a.1100
             This bridge is the root""",
        "expected_fault": "STP Root Guard on Core-SW Gi0/24 blocked the port into 'Root Inconsistent' state after receiving superior BPDUs with Priority 0 from Dist-SW.",
        "osi_layer": 2,
        "concept_tag": "Wireless/L2",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_031_show_output.txt"
    },
    {
        "case_id": "CASE-032",
        "symptom": "Cisco Lightweight Access Points (LAPs) in Branch Office cannot register with the Wireless LAN Controller (WLC) at HQ.",
        "topology_note": "LAPs at Branch (192.168.50.0/24) connect across WAN to HQ WLC (10.200.1.5). CAPWAP control tunnel requires UDP 5246/5247.",
        "show_output": """HQ-Firewall# show access-lists WAN_INSPECT
Extended IP access list WAN_INSPECT
    10 permit tcp any host 10.200.1.5 eq 443
    20 permit tcp any host 10.200.1.5 eq 22
    30 deny ip any host 10.200.1.5 (2481 matches)

Branch-AP# show capwap client status
CAPWAP State: Discovery
Discovery Request Sent Count: 18
Discovery Response Received: 0
WLC IP: 10.200.1.5
Error: Discovery request to 10.200.1.5 timed out.""",
        "expected_fault": "HQ Firewall ACL WAN_INSPECT blocks CAPWAP control/data tunnel traffic (UDP ports 5246 and 5247) between Branch LAPs and the WLC.",
        "osi_layer": 4,
        "concept_tag": "Wireless/L2",
        "severity": "Medium",
        "evidence_file": "data/raw_evidence/case_032_show_output.txt"
    }
]

def generate():
    csv_path = os.path.join(DATA_DIR, "cases.csv")
    fieldnames = [
        "case_id", "symptom", "topology_note", "show_output",
        "expected_fault", "osi_layer", "concept_tag", "severity", "evidence_file"
    ]
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for case in CASES:
            writer.writerow(case)
            
            # Write raw evidence file
            filename = f"case_{case['case_id'].split('-')[1]}_show_output.txt"
            raw_path = os.path.join(RAW_DIR, filename)
            
            content = f"""================================================================================
NETSAGE AI - RAW EVIDENCE CAPTURE
Case ID       : {case['case_id']}
Concept Tag   : {case['concept_tag']}
OSI Layer     : Layer {case['osi_layer']}
Severity      : {case['severity']}
================================================================================

[TOPOLOGY CONTEXT]
{case['topology_note']}

[SYMPTOM DESCRIPTION]
{case['symptom']}

[RAW CISCO IOS CLI EVIDENCE]
{case['show_output']}

[GROUND TRUTH / EXPECTED ROOT CAUSE]
{case['expected_fault']}
================================================================================
"""
            with open(raw_path, "w", encoding="utf-8") as rf:
                rf.write(content)
                
    print(f"Generated {len(CASES)} cases in {csv_path} and {RAW_DIR}")

if __name__ == "__main__":
    generate()
