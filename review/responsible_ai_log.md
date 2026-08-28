# NetSage AI — Responsible AI & Human-in-the-Loop Audit Log

**Project:** NetSage AI (Cisco Internship Project 2: Applied AI + Network Troubleshooting)  
**Lead Evaluator / Reviewer:** Sanjay (HITL Operations Lead)  
**Governance Framework:** Human-in-the-Loop (HITL) Verification, Evidence-Grounded Citation Enforcement, and Deterministic Pre/Post Scoring.

---

## Executive Summary

To prevent automated AI hallucinations from executing disruptive network changes on enterprise infrastructure, **100% of NetSage AI diagnostic recommendations are audited by a human network engineer** before entering production logs.

Across the benchmark dataset of **32 multi-layer incidents**:
- **Accepted (23 / 32 = 71.9%):** AI isolated the exact root cause, cited specific CLI evidence, and provided accurate Cisco IOS remediation commands.
- **Edited (5 / 32 = 15.6%):** AI identified the core fault domain, but human engineers refined remediation syntax (e.g. clearing stale state tables), adjusted OSI layer classifications, or added operational validation steps.
- **Rejected (4 / 32 = 12.5%):** AI produced inaccurate root-cause diagnoses, hallucinated protocol misconfigurations without evidence, or misdiagnosed complex security anomalies.

Below is the detailed post-mortem audit of **6 key failure/correction cases**, explaining why the model failed, the risks of unchecked deployment, and the architectural safeguards engineered as a result.

---

## Case Study 1: CASE-007 — OSPF Neighbor Stuck in EXSTART

### 1. Incident Breakdown
- **Case ID:** `CASE-007` (Layer 3 Routing / OSPF)
- **Symptom:** Core-R1 and Dist-R2 neighbor relationship is stuck in `EXSTART/DBD` state; routing tables do not populate.
- **AI Initial Output:**
  - *Root Cause:* "OSPF authentication MD5 key mismatch between Core-R1 and Dist-R2 on transit link Gi0/0."
  - *Confidence:* `high`
  - *Proposed Fix:* `ip ospf message-digest-key 1 md5 Cisco123`
- **Human Ground Truth:**
  - *Actual Fault:* Interface MTU mismatch on link Gi0/0 (Core-R1 MTU 1500 vs Dist-R2 MTU 1400), causing Database Description (DBD) packets exceeding 1400 bytes to be dropped.
  - *Correct Fix:* `interface GigabitEthernet0/0` -> `ip mtu 1500`.
- **Verdict:** **`Rejected`**

### 2. Root Cause Analysis of AI Failure
- **Why AI Failed:** The model over-indexed on the generic symptom "OSPF neighbor state stuck" and recalled common troubleshooting flashcards (where authentication is a frequent cause). It ignored the explicit lines in `show ip interface Gi0/0` showing `MTU is 1500 bytes` on R1 and `MTU is 1400 bytes` on R2.
- **Operational Danger:** Applying an MD5 key to one router would instantly break all other OSPF adjacencies in that broadcast domain without resolving the underlying MTU deadlock.

### 3. Engineering Safeguards Implemented
- **Prompt Guardrail:** Updated `prompts/diagnose_prompt.md` to penalize confidence unless the cited evidence specifically references the distinguishing parameter (in this case, interface MTU values).
- **Rule Checker Plugin:** Implemented `checker/rules/missing_route.py::check_missing_route()`, which explicitly extracts interface MTUs on OSPF links and flags mismatches deterministically before invoking the LLM.

---

## Case Study 2: CASE-012 — NAT Inside/Outside Direction Inversion

### 1. Incident Breakdown
- **Case ID:** `CASE-012` (Layer 3 / NAT Overload)
- **Symptom:** Internal LAN clients cannot reach the Internet; `show ip nat translations` is completely empty.
- **AI Initial Output:**
  - *Root Cause:* "ACL 1 denies internal outbound NAT traffic, blocking translations on Gi0/1."
  - *Confidence:* `high`
  - *Proposed Fix:* `access-list 1 permit 192.168.1.0 0.0.0.255`
- **Human Ground Truth:**
  - *Actual Fault:* Inverted NAT tags on interfaces: `GigabitEthernet0/0` (LAN) had `ip nat outside` and `GigabitEthernet0/1` (WAN) had `ip nat inside`.
  - *Correct Fix:* Invert tags to `ip nat inside` on Gi0/0 and `ip nat outside` on Gi0/1.
- **Verdict:** **`Rejected`**

### 2. Root Cause Analysis of AI Failure
- **Why AI Failed:** The AI assumed that an empty NAT translation table must be caused by an ACL deny filter, neglecting to inspect the interface-level configuration blocks in the show output.
- **Operational Danger:** Modifying access lists would not restore Internet access because the NAT state engine only evaluates outbound translations when packets traverse from an `inside` interface to an `outside` interface.

### 3. Engineering Safeguards Implemented
- **Prompt Guardrail:** Added a multi-layer diagnostic check in `diagnose_prompt.md` instructing the model to inspect interface attachment directives before diagnosing filter rules.
- **Rule Checker Plugin:** Added `checker/rules/nat_overload_pool.py::check_nat_rules()`, which cross-references interface descriptions (LAN vs WAN) with configured `ip nat inside/outside` tags.

---

## Case Study 3: CASE-018 — Rogue DHCP Server vs. Scope Exhaustion

### 1. Incident Breakdown
- **Case ID:** `CASE-018` (Layer 7 Application / DHCP)
- **Symptom:** Corporate workstations suddenly received IP addresses in `192.168.88.0/24` with default gateway `192.168.88.1` and lost access to intranet servers.
- **AI Initial Output:**
  - *Root Cause:* "DHCP server scope pool exhaustion on corporate core router."
  - *Confidence:* `high`
  - *Proposed Fix:* Expand corporate DHCP pool address range.
- **Human Ground Truth:**
  - *Actual Fault:* Rogue DHCP server plugged into switch port Gi0/8 offering rogue subnet leases because DHCP Snooping was disabled.
  - *Correct Fix:* Enable DHCP Snooping globally and on VLAN 10; shut down unauthorized port Gi0/8.
- **Verdict:** **`Rejected`**

### 2. Root Cause Analysis of AI Failure
- **Why AI Failed:** The model focused on the symptom "lost access to intranet servers" and assumed the DHCP server had stopped providing addresses, failing to recognize that the client *did* receive an IP address, but from an alien subnet (`192.168.88.0/24`) and alien gateway (`192.168.88.1`).
- **Operational Danger:** Expanding the corporate DHCP scope does not prevent the rogue server from winning the DHCP race condition on the local Layer 2 broadcast domain.

### 3. Engineering Safeguards Implemented
- **Prompt Guardrail:** Added few-shot examples illustrating rogue DHCP identification (comparing client assigned default gateway against legitimate corporate SVI addresses).
- **Rule Checker Plugin:** Enhanced `checker/rules/duplicate_ip.py` to inspect DHCP snooping status and compare client gateway subnets against configured SVIs.

---

## Case Study 4: CASE-026 — Split-Brain DNS Forwarder Failure

### 1. Incident Breakdown
- **Case ID:** `CASE-026` (Layer 7 / DNS Resolution)
- **Symptom:** Branch office users cannot resolve internal `.corp.local` hostnames, though public Internet domains resolve normally.
- **AI Initial Output:**
  - *Root Cause:* "DNS Server process on Branch-GW has crashed."
  - *Confidence:* `medium`
  - *Proposed Fix:* Restart DNS daemon on Branch-GW.
- **Human Ground Truth:**
  - *Actual Fault:* Branch-GW name-servers were configured exclusively with public DNS resolvers (`8.8.8.8`), with no conditional forwarding or stub zone for internal zone `corp.local` pointing to AD DNS `10.0.0.5`.
  - *Correct Fix:* Add internal name-server: `ip name-server 10.0.0.5 8.8.8.8`.
- **Verdict:** **`Rejected`**

### 2. Root Cause Analysis of AI Failure
- **Why AI Failed:** The model saw "cannot resolve hostnames" and jumped to a severe service-down conclusion rather than evaluating the DNS query forwarding hierarchy.
- **Operational Danger:** Rebooting the gateway router would disrupt all branch traffic without fixing the split-brain DNS resolution issue.

### 3. Engineering Safeguards Implemented
- **Few-Shot Update:** Added split-brain DNS resolution logic to `prompts/few_shot_examples.md`.

---

## Case Study 5: CASE-015 — Static NAT Typo & Orphaned State Cleanup

### 1. Incident Breakdown
- **Case ID:** `CASE-015` (Layer 3 / Static NAT)
- **Symptom:** External users cannot access DMZ web server via public DNS name; port 443 fails to connect.
- **AI Initial Output:**
  - *Root Cause:* "Static 1-to-1 NAT configuration typo: mapped inside server to 203.0.113.250 instead of 203.0.113.205."
  - *Confidence:* `medium`
  - *Proposed Fix:* `ip nat inside source static 192.168.100.10 203.0.113.205`
- **Human Ground Truth:**
  - *Human Edit:* AI diagnosed the transposed digits correctly, but omitted the critical prerequisite command to remove the existing incorrect static translation (`no ip nat inside source static 192.168.100.10 203.0.113.250`).
- **Verdict:** **`Edited`**

### 2. Root Cause Analysis of Human Edit
- **Why Human Intervention Was Needed:** In Cisco IOS, entering a second static NAT statement for the same inside local IP address without deleting the existing one triggers a CLI error: `% 192.168.100.10 already mapped`.
- **Engineering Action:** Added an operational rule to `prompts/diagnose_prompt.md` requiring that NAT and ACL modification steps explicitly include negation (`no ...`) of obsolete rules prior to adding new rules.

---

## Case Study 6: CASE-020 — DHCP Gateway Lease Hijacking & Table Clearing

### 1. Incident Breakdown
- **Case ID:** `CASE-020` (Layer 7 / DHCP)
- **Symptom:** Default gateway IP 10.50.0.254 becomes unresponsive; ARP table indicates a dynamic workstation MAC.
- **AI Initial Output:**
  - *Root Cause:* "Default gateway IP 10.50.0.254 omitted from 'ip dhcp excluded-address'."
  - *Confidence:* `medium`
  - *Proposed Fix:* `ip dhcp excluded-address 10.50.0.254`
- **Human Ground Truth:**
  - *Human Edit:* Added `clear ip dhcp binding 10.50.0.254` and client notification step.
- **Verdict:** **`Edited`**

### 2. Root Cause Analysis of Human Edit
- **Why Human Intervention Was Needed:** Adding an excluded address prevents *future* leases, but does not invalidate an active lease already held by a client. The rogue lease would persist until expiration (up to 7 days), leaving the gateway unreachable.
- **Engineering Action:** Updated standard operating procedures in `few_shot_examples.md` to include state table flushes (`clear ip dhcp binding`) when remediating active IP collisions.

---

## Summary of Responsible AI Metrics & Continuous Improvements

| Metric | Measurement | Target | Status |
|---|---|---|---|
| **Human Review Coverage** | 100% (32/32 cases audited) | 100% | Met |
| **Evidence Citation Enforcement** | 100% of accepted responses quote CLI tokens | >90% | Met |
| **Deterministic Rule Agreement** | 90.6% rule detection rate | >80% | Met |
| **Unsafe Command Interception** | 4 destructive/ineffective AI proposals blocked | 100% blocked | Met |
| **Prompt Version Iterations** | 3 versions (v1.0 -> v1.1 -> v2.0) | >2 versions | Met |
