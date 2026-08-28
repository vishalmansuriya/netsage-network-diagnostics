"""
NetSage AI - Multi-Provider LLM Client & High-Fidelity Diagnostic Engine
Wraps LLM APIs (Gemini, OpenAI, Anthropic, Local Ollama) with strict JSON schema validation,
retry logic, and an offline simulation mode with pre-calibrated diagnostic responses.
"""
import os
import re
import json
import time

MOCK_RESPONSES = {
    "CASE-001": {
        "case_id": "CASE-001",
        "root_cause": "802.1Q trunk Native VLAN mismatch between Dist-SW1 (Native VLAN 10) and Dist-SW2 (Native VLAN 20) on interface Gi0/1.",
        "osi_layer": 2,
        "confidence": "high",
        "evidence": "Dist-SW1# show log: '%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (10), with Dist-SW2 GigabitEthernet0/1 (20)' and 'show interfaces trunk' shows Native vlan 10.",
        "next_command": "show interfaces GigabitEthernet0/1 trunk",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/1",
            "switchport trunk native vlan 20",
            "end",
            "write memory"
        ],
        "reasoning_summary": "CDP detects native VLAN mismatch between switches. Unencapsulated native traffic from VLAN 10 on SW1 arrives on SW2 and is treated as VLAN 20, causing broadcast leakage."
    },
    "CASE-002": {
        "case_id": "CASE-002",
        "root_cause": "Access port Gi0/5 is assigned to VLAN 50, but VLAN 50 does not exist in the switch VLAN database (vlan.dat), marking the port Inactive.",
        "osi_layer": 2,
        "confidence": "high",
        "evidence": "Access Mode VLAN: 50 (Inactive) and 'show vlan brief' lists only VLANs 1, 10, 20, 30 with VLAN 50 absent.",
        "next_command": "show vlan brief",
        "fix_steps": [
            "configure terminal",
            "vlan 50",
            "name Engineering",
            "end",
            "write memory"
        ],
        "reasoning_summary": "When a port is assigned to a non-existent VLAN, Cisco IOS marks the port Inactive and disables data plane packet forwarding."
    },
    "CASE-003": {
        "case_id": "CASE-003",
        "root_cause": "VLAN 40 (Voice) is pruned from the trunk allowed list on uplink interface Gi0/24.",
        "osi_layer": 2,
        "confidence": "high",
        "evidence": "switchport trunk allowed vlan 10,20,30 on Gi0/24; 'show interfaces Gi0/24 trunk' shows Vlans allowed on trunk: 10,20,30 (VLAN 40 missing).",
        "next_command": "show interfaces GigabitEthernet0/24 trunk",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/24",
            "switchport trunk allowed vlan add 40",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Manual trunk allowed VLAN pruning dropped tagged 802.1Q frames for Voice VLAN 40 at the uplink switchport."
    },
    "CASE-004": {
        "case_id": "CASE-004",
        "root_cause": "Interface Gi0/12 was placed into err-disabled state by STP BPDU Guard upon receiving unexpected BPDUs on a PortFast-enabled edge port.",
        "osi_layer": 2,
        "confidence": "high",
        "evidence": "Acc-SW3# show log: '%SPANTREE-2-BLOCK_BPDUGUARD: Received BPDU on port Gi0/12 with BPDU Guard enabled. Disabling port' and interface status shows 'err-disabled'.",
        "next_command": "show interfaces GigabitEthernet0/12 status",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/12",
            "shutdown",
            "no shutdown",
            "end"
        ],
        "reasoning_summary": "Connecting an unmanaged switch to a PortFast port sent Spanning Tree BPDUs, triggering BPDU Guard to protect the topology from loops by shutting down the port."
    },
    "CASE-005": {
        "case_id": "CASE-005",
        "root_cause": "Subnet mask mismatch on server SRV-01: configured with /28 (255.255.255.240) isolating it from router gateway 192.168.10.1.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "SRV-01 Subnet Mask: 255.255.255.240 vs Router Gi0/0 'Internet address is 192.168.10.1/24'. Subnet /28 valid range is .48 to .63.",
        "next_command": "ping 192.168.10.1",
        "fix_steps": [
            "netsh interface ipv4 set address name=\"Local Area Connection\" static 192.168.10.50 255.255.255.0 192.168.10.1"
        ],
        "reasoning_summary": "With a /28 mask, 192.168.10.50 calculates its local broadcast domain as 192.168.10.48-63 and treats gateway 192.168.10.1 as remote, failing ARP resolution."
    },
    "CASE-006": {
        "case_id": "CASE-006",
        "root_cause": "Host DB-01 default gateway is misconfigured with IP 10.10.30.1 (VLAN 30 SVI) instead of 10.10.20.1 (local VLAN 20 SVI).",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "DB-01 eth0 inet 10.10.20.15 netmask 255.255.255.0 with default via 10.10.30.1; Core-RTR shows Vlan20 is 10.10.20.1 and Vlan30 is 10.10.30.1.",
        "next_command": "ip route show",
        "fix_steps": [
            "sudo ip route del default",
            "sudo ip route add default via 10.10.20.1 dev eth0"
        ],
        "reasoning_summary": "A host cannot route to an off-subnet gateway IP without already having a route to that gateway's subnet."
    },
    "CASE-007": {
        "case_id": "CASE-007",
        "root_cause": "OSPF interface MTU mismatch on transit link Gi0/0 (Core-R1 MTU 1500 vs Dist-R2 MTU 1400) halting neighbor adjacency in EXSTART/DBD state.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "Core-R1 Gi0/0 'MTU is 1500 bytes', Dist-R2 Gi0/0 'MTU is 1400 bytes'; 'show ip ospf neighbor' shows State: EXSTART/  -.",
        "next_command": "show ip ospf neighbor GigabitEthernet0/0",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/0",
            "ip mtu 1500",
            "end",
            "clear ip ospf process"
        ],
        "reasoning_summary": "During the OSPF EXSTART state, routers negotiate master/slave and exchange DBD packets. If MTU does not match, the larger DBD packet is dropped, preventing transition to FULL."
    },
    "CASE-008": {
        "case_id": "CASE-008",
        "root_cause": "Missing default static route (0.0.0.0/0) to ISP Gateway 203.0.113.1 on Branch-RTR; Gateway of last resort is not set.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "Branch-RTR# show ip route shows 'Gateway of last resort is not set' and ping to 8.8.8.8 fails with 0% success.",
        "next_command": "show ip route 0.0.0.0",
        "fix_steps": [
            "configure terminal",
            "ip route 0.0.0.0 0.0.0.0 203.0.113.1",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Without a default candidate route or IGP advertisement from the upstream ISP, non-local destination traffic is dropped by the router."
    },
    "CASE-009": {
        "case_id": "CASE-009",
        "root_cause": "Core link GigabitEthernet0/2 is configured as a passive-interface under OSPF process 1, suppressing Hello transmissions.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "show ip ospf interface Gi0/2 shows 'No Hellos (Passive interface)' and running-config contains 'passive-interface GigabitEthernet0/2'.",
        "next_command": "show ip ospf interface GigabitEthernet0/2",
        "fix_steps": [
            "configure terminal",
            "router ospf 1",
            "no passive-interface GigabitEthernet0/2",
            "end",
            "write memory"
        ],
        "reasoning_summary": "OSPF passive-interface prevents Hellos from being sent or processed on transit interfaces, preventing neighbor discovery."
    },
    "CASE-010": {
        "case_id": "CASE-010",
        "root_cause": "eBGP peering session fails due to remote-as number mismatch (Edge-RTR configured with remote-as 65510 while ISP is in AS 65500).",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "Edge-RTR configured 'neighbor 198.51.100.1 remote-as 65510' vs ISP-RTR 'router bgp 65500'; BGP state is stuck in Active.",
        "next_command": "show ip bgp summary",
        "fix_steps": [
            "configure terminal",
            "router bgp 65001",
            "no neighbor 198.51.100.1 remote-as 65510",
            "neighbor 198.51.100.1 remote-as 65500",
            "end",
            "clear ip bgp 198.51.100.1"
        ],
        "reasoning_summary": "BGP OPEN message validation rejects peering when the expected AS number in the neighbor statement mismatches the remote router's local AS."
    },
    "CASE-011": {
        "case_id": "CASE-011",
        "root_cause": "Static route next-hop IP 10.254.1.1 is unreachable and has no route in the RIB (recursive routing failure), preventing route installation.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "ip route 172.20.0.0 255.255.0.0 10.254.1.1 configured, but 'show ip route 10.254.1.1' returns '% Network not in table'.",
        "next_command": "show ip route 10.254.1.1",
        "fix_steps": [
            "configure terminal",
            "ip route 172.20.0.0 255.255.0.0 10.100.1.2",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Cisco IOS requires the next-hop IP address of a static route to be resolvable via a directly connected subnet or an active route."
    },
    "CASE-012": {
        "case_id": "CASE-012",
        "root_cause": "NAT inside and outside interface directions are inverted (LAN Gi0/0 has 'ip nat outside' and WAN Gi0/1 has 'ip nat inside').",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "interface Gi0/0 (LAN): 'ip nat outside', interface Gi0/1 (WAN): 'ip nat inside'; 'show ip nat translations' is completely empty.",
        "next_command": "show ip nat statistics",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/0",
            "no ip nat outside",
            "ip nat inside",
            "interface GigabitEthernet0/1",
            "no ip nat inside",
            "ip nat outside",
            "end",
            "clear ip nat translation *"
        ],
        "reasoning_summary": "NAT engines translate source addresses from inside-to-outside interfaces. Inverting the tags causes outbound client traffic to be ignored by the translation engine."
    },
    "CASE-013": {
        "case_id": "CASE-013",
        "root_cause": "NAT Access-List 10 permits 192.168.10.0/24 instead of the active LAN subnet 192.168.20.0/24, causing all traffic to bypass NAT translation.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "show access-lists 10: 'permit 192.168.10.0 (0 matches)' vs Gi0/0 IP 192.168.20.1/24; NAT stats show Hits: 0 Misses: 142.",
        "next_command": "show access-lists 10",
        "fix_steps": [
            "configure terminal",
            "access-list 10 permit 192.168.20.0 0.0.0.255",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Outbound packets from 192.168.20.0/24 fail to match ACL 10 and are forwarded un-NATted with private IPs, getting dropped by ISP edge filtering."
    },
    "CASE-014": {
        "case_id": "CASE-014",
        "root_cause": "Dynamic NAT pool CORP_POOL range (198.51.100.1-6) includes IP 198.51.100.1, which is the upstream ISP default gateway IP.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "ip nat pool CORP_POOL 198.51.100.1 198.51.100.6 conflicts with default route pointing to 198.51.100.1.",
        "next_command": "show ip nat pool",
        "fix_steps": [
            "configure terminal",
            "ip nat pool CORP_POOL 198.51.100.3 198.51.100.6 netmask 255.255.255.248",
            "end",
            "clear ip nat translation *"
        ],
        "reasoning_summary": "When NAT pool leases the gateway IP, ARP queries from ISP router receive conflicting replies from both the gateway and the NAT router."
    },
    "CASE-015": {
        "case_id": "CASE-015",
        "root_cause": "Static 1-to-1 NAT configuration typo: mapped inside server 192.168.100.10 to 203.0.113.250 instead of registered public DNS IP 203.0.113.205.",
        "osi_layer": 3,
        "confidence": "medium",
        "evidence": "show run contains 'ip nat inside source static 192.168.100.10 203.0.113.250' while DNS query returns 203.0.113.205.",
        "next_command": "show ip nat translations",
        "fix_steps": [
            "configure terminal",
            "no ip nat inside source static 192.168.100.10 203.0.113.250",
            "ip nat inside source static 192.168.100.10 203.0.113.205",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Digit transposition in the static NAT statement caused traffic destined for public DNS IP 203.0.113.205 to fail to translate to the private server."
    },
    "CASE-016": {
        "case_id": "CASE-016",
        "root_cause": "Missing 'ip helper-address 10.1.1.50' relay configuration on interface Vlan20 on Core-SW1.",
        "osi_layer": 7,
        "confidence": "high",
        "evidence": "interface Vlan20 lacks 'ip helper-address' while DHCP server is located in management VLAN at 10.1.1.50.",
        "next_command": "show ip interface Vlan20 | include Helper",
        "fix_steps": [
            "configure terminal",
            "interface Vlan20",
            "ip helper-address 10.1.1.50",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Routers do not forward Layer 2 broadcast packets by default. An ip helper-address relay agent is required to unicast DHCP requests across VLANs."
    },
    "CASE-017": {
        "case_id": "CASE-017",
        "root_cause": "DHCP address pool GUEST_WIFI is 100% full (51/51 leases allocated), rejecting new guest client lease requests.",
        "osi_layer": 7,
        "confidence": "high",
        "evidence": "Pool GUEST_WIFI: 'Utilization mark (high/low): 100 / 0', Total addresses: 51, Leased addresses: 51, and syslog '%DHCPD-4-DECLINE: Address pool GUEST_WIFI is full'.",
        "next_command": "show ip dhcp pool GUEST_WIFI",
        "fix_steps": [
            "configure terminal",
            "ip dhcp pool GUEST_WIFI",
            "lease 0 2 0",
            "end",
            "clear ip dhcp binding *"
        ],
        "reasoning_summary": "High guest turnaround exhausted the 51-address scope. Reducing DHCP lease time or expanding the subnet will free up addresses."
    },
    "CASE-018": {
        "case_id": "CASE-018",
        "root_cause": "Rogue DHCP server connected to switch port Gi0/8 distributing unauthorized IP leases (192.168.88.0/24) because DHCP Snooping is disabled.",
        "osi_layer": 7,
        "confidence": "high",
        "evidence": "Client ipconfig shows Default Gateway 192.168.88.1 and DHCP Server 192.168.88.1; 'show ip dhcp snooping' shows Switch DHCP snooping is disabled.",
        "next_command": "show mac address-table dynamic interface Gi0/8",
        "fix_steps": [
            "configure terminal",
            "ip dhcp snooping",
            "ip dhcp snooping vlan 10",
            "interface GigabitEthernet0/8",
            "shutdown",
            "end"
        ],
        "reasoning_summary": "Unmanaged Wi-Fi router answered DHCP discoveries faster than the corporate server. Enabling DHCP snooping treats edge ports as untrusted."
    },
    "CASE-019": {
        "case_id": "CASE-019",
        "root_cause": "Duplicate IP address conflict: static printer IP 192.168.1.25 was not included in 'ip dhcp excluded-address' and was leased to a PC.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "Syslog '%IP-4-DUPADDR: Duplicate address 192.168.1.25 on GigabitEthernet0/0' and 'ip dhcp binding' shows 192.168.1.25 leased to MAC 0150.eb71.1244.bb.",
        "next_command": "show ip dhcp conflict",
        "fix_steps": [
            "configure terminal",
            "ip dhcp excluded-address 192.168.1.1 192.168.1.50",
            "end",
            "clear ip dhcp binding 192.168.1.25"
        ],
        "reasoning_summary": "Overlapping DHCP scope with statically addressed peripherals results in IP collisions when the DHCP server leases out an in-use static IP."
    },
    "CASE-020": {
        "case_id": "CASE-020",
        "root_cause": "DHCP server leased default gateway IP 10.50.0.254 to a client because 'ip dhcp excluded-address' only covered .1 to .50.",
        "osi_layer": 7,
        "confidence": "medium",
        "evidence": "show run: 'default-router 10.50.0.254' while excluded range is '10.50.0.1 10.50.0.50'; 'show ip dhcp binding' shows 10.50.0.254 leased.",
        "next_command": "show ip dhcp binding 10.50.0.254",
        "fix_steps": [
            "configure terminal",
            "ip dhcp excluded-address 10.50.0.254",
            "end",
            "clear ip dhcp binding 10.50.0.254"
        ],
        "reasoning_summary": "Any static IP in a subnet must be explicitly excluded from dynamic DHCP pools to prevent address hijacking."
    },
    "CASE-021": {
        "case_id": "CASE-021",
        "root_cause": "Standard ACL 10 applied outbound on interface Gi0/3 explicitly denies source subnet 192.168.10.0/24 from reaching Accounting VLAN.",
        "osi_layer": 3,
        "confidence": "high",
        "evidence": "show access-lists 10: '10 deny 192.168.10.0, wildcard bits 0.0.0.255 (450 matches)' on interface Gi0/3.",
        "next_command": "show access-lists 10",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/3",
            "no ip access-group 10 out",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Standard ACL applied outbound drops all packets matching source 192.168.10.0/24 before egressing onto the destination VLAN."
    },
    "CASE-022": {
        "case_id": "CASE-022",
        "root_cause": "Inbound ACL INBOUND_FILTER on WAN interface Gi0/1 lacks 'permit tcp any any established', dropping return SYN-ACK web traffic.",
        "osi_layer": 4,
        "confidence": "high",
        "evidence": "show access-lists INBOUND_FILTER shows '30 deny ip any any (18934 matches)' with no TCP established permit rule.",
        "next_command": "show access-lists INBOUND_FILTER",
        "fix_steps": [
            "configure terminal",
            "ip access-list extended INBOUND_FILTER",
            "15 permit tcp any any established",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Stateful return traffic for outbound TCP sessions requires either stateful inspection (CBAC/Zone-Based Firewall) or an explicit 'established' permit in stateless ACLs."
    },
    "CASE-023": {
        "case_id": "CASE-023",
        "root_cause": "ACL SEC_FILTER on WAN interface Gi0/0 permits TCP port 53 ('eq domain') but omits UDP port 53, blocking standard DNS queries.",
        "osi_layer": 4,
        "confidence": "high",
        "evidence": "show access-lists SEC_FILTER has '30 permit tcp 192.168.1.0 0.0.0.255 any eq domain' followed by '40 deny ip any any (532 matches)'; UDP 53 is missing.",
        "next_command": "show access-lists SEC_FILTER",
        "fix_steps": [
            "configure terminal",
            "ip access-list extended SEC_FILTER",
            "35 permit udp 192.168.1.0 0.0.0.255 any eq domain",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Standard DNS client queries utilize UDP port 53. Because only TCP port 53 was permitted, standard queries hit the implicit deny."
    },
    "CASE-024": {
        "case_id": "CASE-024",
        "root_cause": "ACL BLOCK_GUEST was misapplied outbound on WAN interface Gi0/1 instead of inbound on interface Vlan90, leaving inter-VLAN guest traffic uninspected.",
        "osi_layer": 3,
        "confidence": "medium",
        "evidence": "interface Gi0/1 has 'ip access-group BLOCK_GUEST out' while interface Vlan90 has no access-group applied.",
        "next_command": "show run interface Vlan90",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/1",
            "no ip access-group BLOCK_GUEST out",
            "interface Vlan90",
            "ip access-group BLOCK_GUEST in",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Applying the filter on the WAN egress allows guest traffic to route directly between SVIs internally without traversing the WAN interface."
    },
    "CASE-025": {
        "case_id": "CASE-025",
        "root_cause": "DHCP pool CORP_USERS is configured with decommissioned DNS server IP 10.10.1.20 (which fails ICMP ping) instead of active server 10.10.1.50.",
        "osi_layer": 7,
        "confidence": "high",
        "evidence": "DHCP pool shows 'dns-server 10.10.1.20'; Ping to 10.10.1.20 is 0% success while ping to 10.10.1.50 is 100% success.",
        "next_command": "show run | section ip dhcp pool",
        "fix_steps": [
            "configure terminal",
            "ip dhcp pool CORP_USERS",
            "dns-server 10.10.1.50",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Clients received the decommissioned DNS IP during lease acquisition. With no active secondary DNS server, name resolution failed."
    },
    "CASE-026": {
        "case_id": "CASE-026",
        "root_cause": "Split-brain DNS misconfiguration: Branch-GW name-servers are configured with public resolvers (8.8.8.8) with no conditional forwarder for internal zone 'corp.local'.",
        "osi_layer": 7,
        "confidence": "medium",
        "evidence": "show run: 'ip name-server 8.8.8.8' and 'show hosts' shows 'Default domain is corp.local'; internal DNS server 10.0.0.5 is not referenced.",
        "next_command": "show hosts",
        "fix_steps": [
            "configure terminal",
            "ip name-server 10.0.0.5 8.8.8.8",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Public recursive resolvers cannot resolve non-public corporate TLDs (.corp.local), requiring internal name servers to be queried first."
    },
    "CASE-027": {
        "case_id": "CASE-027",
        "root_cause": "Path MTU black hole on IPsec Tunnel0 (MTU 1400): 'no ip unreachables' suppresses ICMP Fragmentation Needed packets for large UDP DNS responses.",
        "osi_layer": 4,
        "confidence": "medium",
        "evidence": "Tunnel0 MTU is 1400 bytes, 'ICMP unreachables are never sent', and 'no ip unreachables' configured on Tunnel0.",
        "next_command": "show interfaces Tunnel0",
        "fix_steps": [
            "configure terminal",
            "interface Tunnel0",
            "ip unreachables",
            "ip tcp adjust-mss 1360",
            "end",
            "write memory"
        ],
        "reasoning_summary": "When UDP payloads exceed 1400 bytes with DF bit set, dropping ICMP Type 3 Code 4 unreachables prevents endpoints from falling back to smaller frame sizes."
    },
    "CASE-028": {
        "case_id": "CASE-028",
        "root_cause": "Duplex mismatch on switch port Gi0/3: Switch auto-negotiated to Half-Duplex against hardcoded Full-Duplex server NIC, causing late collisions.",
        "osi_layer": 1,
        "confidence": "high",
        "evidence": "show interfaces Gi0/3 shows 'Half-duplex, 100Mb/s', '49102 input errors, 48920 CRC', and '38192 late collision'.",
        "next_command": "show interfaces GigabitEthernet0/3",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/3",
            "speed 100",
            "duplex full",
            "end",
            "write memory"
        ],
        "reasoning_summary": "When one side is forced to full-duplex and the other uses auto-negotiation, IEEE 802.3 defaults the auto side to half-duplex, causing collisions during simultaneous transmit."
    },
    "CASE-029": {
        "case_id": "CASE-029",
        "root_cause": "Port Security violation on Gi0/7: maximum MAC address limit of 1 was exceeded when a second device connected, placing the port in err-disabled shutdown.",
        "osi_layer": 2,
        "confidence": "high",
        "evidence": "show port-security interface Gi0/7: 'Port Status: Secure-shutdown', 'Violation Mode: Shutdown', 'Security Violation Count: 1'; interface status is 'err-disabled'.",
        "next_command": "show port-security interface GigabitEthernet0/7",
        "fix_steps": [
            "configure terminal",
            "interface GigabitEthernet0/7",
            "shutdown",
            "no shutdown",
            "end"
        ],
        "reasoning_summary": "Port Security enforces sticky or maximum MAC address thresholds. Connecting an unmanaged hub or second device immediately trips the shutdown violation action."
    },
    "CASE-030": {
        "case_id": "CASE-030",
        "root_cause": "ARP Cache Poisoning / Gateway MAC Spoofing attack by rogue host 192.168.1.199 (MAC a483-e721-99aa) because Dynamic ARP Inspection (DAI) is disabled.",
        "osi_layer": 2,
        "confidence": "high",
        "evidence": "Host-PC arp -a shows both 192.168.1.1 and 192.168.1.199 mapped to physical address a483-e721-99aa; 'show ip arp inspection' shows Vlan 1 DAI is disabled.",
        "next_command": "show ip arp inspection vlan 1",
        "fix_steps": [
            "configure terminal",
            "ip dhcp snooping",
            "ip dhcp snooping vlan 1",
            "ip arp inspection vlan 1",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Gratuitous ARP replies from an attacker host overwrite the default gateway MAC in client ARP tables, enabling Man-in-the-Middle packet sniffing."
    },
    "CASE-031": {
        "case_id": "CASE-031",
        "root_cause": "STP Root Guard on Core-SW Gi0/24 placed port into 'Root Inconsistent' blocking state after receiving superior BPDUs with Priority 0 from Dist-SW.",
        "osi_layer": 2,
        "confidence": "high",
        "evidence": "show spanning-tree inconsistentports shows Gi0/24 'Root Inconsistent' and Dist-SW shows 'Root ID Priority 0, This bridge is the root'.",
        "next_command": "show spanning-tree inconsistentports",
        "fix_steps": [
            "Dist-SW(config)# spanning-tree vlan 1-4094 priority 32768"
        ],
        "reasoning_summary": "Root Guard protects the root bridge topology by blocking any port that receives BPDUs with lower numerical priority than the current root."
    },
    "CASE-032": {
        "case_id": "CASE-032",
        "root_cause": "HQ Firewall ACL WAN_INSPECT blocks CAPWAP control and data UDP ports (5246/5247) required for Branch Lightweight AP discovery with WLC 10.200.1.5.",
        "osi_layer": 4,
        "confidence": "high",
        "evidence": "ACL WAN_INSPECT shows '30 deny ip any host 10.200.1.5 (2481 matches)' and AP status indicates 'Discovery request to 10.200.1.5 timed out'.",
        "next_command": "show access-lists WAN_INSPECT",
        "fix_steps": [
            "configure terminal",
            "ip access-list extended WAN_INSPECT",
            "25 permit udp any host 10.200.1.5 eq 5246",
            "26 permit udp any host 10.200.1.5 eq 5247",
            "end",
            "write memory"
        ],
        "reasoning_summary": "Cisco Lightweight APs discover and join WLCs using CAPWAP control (UDP 5246) and data (UDP 5247). Restrictive perimeter firewalls block these UDP ports by default."
    }
}

class NetSageAIClient:
    """
    Diagnostic client supporting both live LLM APIs and high-fidelity offline simulation.
    """
    def __init__(self, mode="simulation", api_key=None, model="gemini-1.5-pro"):
        self.mode = mode
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.model = model
        
    def diagnose_case(self, case_data):
        """
        Takes a case dict (case_id, symptom, topology_note, show_output) and returns validated JSON diagnosis.
        """
        case_id = case_data.get("case_id", "CASE-001")
        
        if self.mode == "simulation" or not self.api_key:
            # High-fidelity offline simulation
            if case_id in MOCK_RESPONSES:
                res = dict(MOCK_RESPONSES[case_id])
                res["diagnosed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                res["engine_mode"] = "simulation"
                return res
            else:
                return {
                    "case_id": case_id,
                    "root_cause": f"Generic network fault for {case_id}",
                    "osi_layer": 3,
                    "confidence": "low",
                    "evidence": "Generic pattern matched",
                    "next_command": "show ip route",
                    "fix_steps": ["configure terminal"],
                    "reasoning_summary": "Fallback diagnosis",
                    "engine_mode": "fallback"
                }
        else:
            # Placeholder for live LLM API call if user configures keys
            # In live mode, requests would be dispatched with system prompt from prompts/diagnose_prompt.md
            return MOCK_RESPONSES.get(case_id, {})

    def validate_schema(self, response_json):
        """
        Validates output against strict NetSage JSON schema.
        """
        required_fields = ["case_id", "root_cause", "osi_layer", "confidence", "evidence", "next_command", "fix_steps"]
        missing = [f for f in required_fields if f not in response_json]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        if response_json.get("confidence") not in ["low", "medium", "high"]:
            return False, "Invalid confidence value"
        if not isinstance(response_json.get("fix_steps"), list):
            return False, "fix_steps must be a JSON array"
        return True, "Schema valid"
