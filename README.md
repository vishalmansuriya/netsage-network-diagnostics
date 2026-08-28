#  NetSage AI — Applied AI Network Diagnostic & HITL Governance Platform

[![Cisco Internship Project](https://img.shields.io/badge/Cisco_Internship-Project_2-00bceb.svg?style=for-the-badge&logo=cisco&logoColor=white)](https://cisco.com)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776ab.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Human in the Loop](https://img.shields.io/badge/Governance-Human--in--the--Loop-10b981.svg?style=for-the-badge&logo=shield&logoColor=white)]()
[![Deterministic Rule Engine](https://img.shields.io/badge/Rule_Engine-90.6%25_Hit_Rate-8b5cf6.svg?style=for-the-badge)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)]()

> **NetSage AI** is an enterprise-grade network troubleshooting and diagnostic system developed for the **Cisco Internship (Project 2)**. It bridges the gap between generative AI models and mission-critical network reliability by integrating **deterministic rule checking**, **evidence-grounded LLM inference**, and **strict Human-in-the-Loop (HITL) audit logging**.

---

##  Table of Contents

- [Executive Summary](#-executive-summary)
- [System Architecture & Workflow](#-system-architecture--workflow)
- [Repository Structure](#-repository-structure)
- [Dataset & OSI Layer Coverage](#-dataset--osi-layer-coverage)
- [Deterministic Rule Checker Engine](#-deterministic-rule-checker-engine)
- [Prompt Engineering & Evidence Grounding](#-prompt-engineering--evidence-grounding)
- [Human-in-the-Loop Audit & Responsible AI](#-human-in-the-loop-audit--responsible-ai)
- [Interactive Analytics Web Dashboard](#-interactive-analytics-web-dashboard)
- [Quick Start & Execution Guide](#-quick-start--execution-guide)
- [Evaluation Rubric Compliance Matrix](#-evaluation-rubric-compliance-matrix)
- [Team & Contributions](#-team--contributions)

---

##  Executive Summary

Large language models troubleshooting production routers and switches often hallucinate causes, misdiagnose multi-layer anomalies, or suggest dangerous configuration commands.

**NetSage AI solves this through a dual-layer architecture:**
1. **Independent Deterministic Rule Checker:** Runs before and after AI inference to evaluate ground truth math (subnet boundaries, duplicate IPs, gateway reachability, err-disabled interfaces).
2. **Evidence-Grounded AI Prompts:** Forces the AI to quote exact lines from Cisco IOS `show` command outputs before making a diagnosis.
3. **Mandatory Human Review (Zero Rubber-Stamping):** 100% of diagnoses produce an auditable review log marked as `Accepted` (71.9%), `Edited` (15.6%), or `Rejected` (12.5%).

---

##  System Architecture & Workflow

```
+-------------------------------------------------------------------------+
|                  32+ Cisco IOS Incident Cases (data/cases.csv)          |
|            Synthetic CLI Evidence (data/raw_evidence/)                  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|               Deterministic Rule Checker (8 Python Plugins)             |
|          Evaluates IP overlap, masks, gateways, VLANs, MTU, ACLs        |
+------------------------------------+------------------------------------+
                                     |
                    +----------------+----------------+
                    |                                 |
                    v                                 v
    +---------------+---------------+ +---------------+---------------+
    |  Pre-Diagnosis Validation     | |   Evidence-Grounded AI Model  |
    |  (Deterministic Ground Truth) | |   (Prompt v2.0 with Citations)|
    +---------------+---------------+ +---------------+---------------+
                    |                                 |
                    +----------------+----------------+
                                     | (Strict JSON Output)
                                     v
+------------------------------------+------------------------------------+
|               Human-in-the-Loop Audit (review/review_log.csv)           |
|                Human Verdict: Accepted / Edited / Rejected              |
+------------------------------------+------------------------------------+
                                     |
                    +----------------+----------------+
                    |                                 |
                    v                                 v
    +---------------+---------------+ +---------------+---------------+
    |   Responsible AI Post-Mortems | |  Interactive Web Dashboard    |
    |   (6 Documented Failure Cases)| |  (Live Charts & 4-Way Diff)   |
    +-------------------------------+ +-------------------------------+
```

---

##  Repository Structure

Every folder maps 1:1 onto the required deliverables table in the internship brief:

```
ciscovip/
├── README.md                          # Master documentation & evaluation matrix
├── data/
│   ├── cases.csv                      # 32 benchmark network cases with ground truth & OSI tags
│   ├── schema.md                      # Comprehensive dataset schema and column taxonomy
│   └── raw_evidence/                  # 32 synthetically generated Cisco IOS-style evidence files
│       ├── case_001_show_output.txt
│       └── ... (up to case_032_show_output.txt)
│
├── prompts/
│   ├── diagnose_prompt.md             # Core structured JSON diagnostic prompt (v2.0)
│   ├── few_shot_examples.md           # 3 multi-domain worked few-shot examples (VLAN, OSPF, DHCP)
│   └── prompt_versions/               # Version history (v1.0 baseline, v1.1 citations, changelog)
│       ├── v1.0_baseline.md
│       ├── v1.1_evidence_enforced.md
│       └── prompt_changelog.md
│
├── checker/
│   ├── rule_checker.py                # Deterministic rule engine CLI runner
│   ├── sample_output.txt              # Sample CLI output showing rule validation on test cases
│   └── rules/                         # 8 modular deterministic rule plugins
│       ├── duplicate_ip.py            # Detects duplicate IPs, ARP spoofing, unexcluded gateway leases
│       ├── mask_mismatch.py           # Validates host subnet prefix vs router interface boundary
│       ├── gateway_mismatch.py        # Identifies off-subnet gateways and unreachable servers
│       ├── interface_down.py          # Checks BPDU Guard, Port Security, duplex collisions, Root Guard
│       ├── missing_vlan.py            # Detects native VLAN mismatch, missing vlan.dat, trunk pruning
│       ├── missing_route.py           # Evaluates default route omission, OSPF MTU, BGP AS mismatch
│       ├── acl_deny_implicit.py       # Identifies missing established permits, DNS port typos
│       └── nat_overload_pool.py       # Detects inverted NAT interfaces, pool overlap, scope exhaustion
│
├── pipeline/
│   ├── run_diagnosis.py               # Batch orchestrator running diagnosis across all cases
│   ├── ai_client.py                   # Multi-provider LLM client with JSON validation & simulation
│   └── responses/                     # 32 structured AI JSON responses
│       ├── case_001_response.json
│       └── ...
│
├── review/
│   ├── review_log.csv                 # 32-row HITL audit log (Accepted: 71.9%, Edited: 15.6%, Rejected: 12.5%)
│   └── responsible_ai_log.md          # In-depth post-mortem analyses of 6 failure/correction cases
│
├── dashboard/
│   ├── dashboard.py                   # Python metric aggregator and CLI summary generator
│   ├── metrics.json                   # Aggregated statistics JSON for dashboard consumption
│   ├── index.html                     # Modern, terminal/hacker style analytics dashboard
│   ├── styles.css                     # Dark & light theme variables and responsive layout
│   └── app.js                         # Dynamic Chart.js engine, case explorer, and 4-way diff viewer
│
├── demo/
│   ├── demo_script.md                 # 5–10 minute presentation script and broken-case talking points
│   └── run_demo.bat                   # 1-click automated batch launcher for live presentation
│
└── scripts/
    └── build_data.py                  # Dataset and raw evidence generator
```

---

##  Dataset & OSI Layer Coverage

The dataset contains **32 synthetically generated but internally consistent cases** with Cisco IOS-style CLI syntax. `scripts/build_data.py` is the data source: it materializes `data/cases.csv` and the 32 files in `data/raw_evidence/`. The cases are validated for topology, IP-addressing, subnet-mask, and VLAN coherence; the evidence files are generated test artifacts, not captures from live network devices.

| Concept Tag | Case Count | % of Dataset | Tested Scenarios |
|---|---|---|---|
| **Routing** | 7 | 21.9% | OSPF MTU Mismatch, Missing Default Route, Passive Interface, BGP AS Mismatch, Recursive Lookup Failure, Subnet Mask Mismatch, Default Gateway Mismatch |
| **Wireless / L2** | 6 | 18.8% | BPDU Guard Err-Disable, Duplex Mismatch Late Collisions, Port Security Violation, ARP Spoofing / DAI, STP Root Guard Block, CAPWAP Tunnel ACL Drop |
| **DHCP** | 5 | 15.6% | DHCP Relay Helper Missing, Scope Pool Exhaustion, Rogue DHCP Server, Duplicate IP Conflict, Gateway IP Lease Hijacking |
| **NAT / PAT** | 4 | 12.5% | Inside/Outside Interface Inversion, Overload ACL Subnet Mismatch, Pool Overlap with ISP Gateway, Static NAT DNS Typo |
| **ACL / Security** | 4 | 12.5% | Inter-VLAN Standard ACL Drop, Missing TCP Established Keyword, DNS UDP 53 vs TCP 53 Typo, ACL Applied on Wrong Interface |
| **VLAN / Trunking** | 3 | 9.4% | 802.1Q Native VLAN Mismatch, Access Port in Non-Existent VLAN, Trunk Allowed List Pruned Critical VLAN |
| **DNS Resolution** | 3 | 9.4% | Decommissioned Primary DNS IP, Split-Brain Forwarder Misconfiguration, Path MTU IPsec Tunnel Blackhole |

---

##  Deterministic Rule Checker Engine

The deterministic engine (`checker/rule_checker.py`) runs independently of the AI and serves as our objective ground truth:

```bash
python checker/rule_checker.py --all --save-sample
```

### Verified Rule Engine Performance:
- **Total Cases Evaluated:** 32
- **Violations Flagged:** 29
- **Deterministic Detection Rate:** **90.6%**
- **Sample Output:** Saved at [checker/sample_output.txt](file:///c:/Users/Sanjay/Documents/antigravity/ciscovip/checker/sample_output.txt).

---

##  Prompt Engineering & Evidence Grounding

The AI diagnostic prompt (`prompts/diagnose_prompt.md`) enforces strict JSON schema and evidence citations:

```json
{
  "case_id": "CASE-007",
  "root_cause": "OSPF interface MTU mismatch on link Gi0/0",
  "osi_layer": 3,
  "confidence": "high",
  "evidence": "Core-R1 MTU is 1500 bytes vs Dist-R2 MTU is 1400 bytes",
  "next_command": "show ip ospf neighbor GigabitEthernet0/0",
  "fix_steps": [
    "configure terminal",
    "interface GigabitEthernet0/0",
    "ip mtu 1500",
    "end"
  ]
}
```

---

##  Human-in-the-Loop Audit & Responsible AI

Every AI diagnosis is reviewed by a human network engineer before acceptance:

```
================================================================================
NETSAGE AI — PERFORMANCE & HUMAN-IN-THE-LOOP METRICS SUMMARY
================================================================================
Total Evaluated Cases      : 32
AI Acceptance Rate         : 71.9% (23/32 cases)
Human Edited Rate          : 15.6% (5/32 cases)
Human Rejected Rate        : 12.5% (4/32 cases)
Deterministic Rule Hit Rate: 90.6% (29/32 cases caught deterministically)
================================================================================
```

### Documented Failure Case Studies in `review/responsible_ai_log.md`:
1. **CASE-007 (OSPF MTU Mismatch — Rejected):** AI hallucinated MD5 authentication failure because neighbor was in EXSTART. Caught by human reviewer and deterministic MTU rule.
2. **CASE-012 (NAT Inversion — Rejected):** AI blamed an ACL rule when the actual fault was inverted `ip nat inside/outside` tags.
3. **CASE-018 (Rogue DHCP Server — Rejected):** AI misdiagnosed symptom as local pool exhaustion, missing that the client received an alien gateway `192.168.88.1`.
4. **CASE-026 (Split-Brain DNS — Rejected):** AI hallucinated a service crash instead of inspecting the public vs internal forwarding hierarchy.
5. **CASE-015 (Static NAT Typo — Edited):** AI diagnosed transposed digits but forgot mandatory `no ip nat inside source static` deletion prerequisite.
6. **CASE-020 (DHCP Gateway Hijack — Edited):** AI proposed excluded-address but omitted clearing active 7-day hijacked lease table.

---

##  Interactive Analytics Web Dashboard

The web dashboard (`dashboard/index.html`) features a modern **terminal/hacker dark-mode aesthetic** with:
- **Live Terminal Trace (Hero Section):** Real-time typing animation with interactive `[ACCEPT]`, `[EDIT]`, and `[REJECT]` buttons.
- **KPI Metrics Cards:** Total cases, AI Acceptance rate, Human Edit rate, Human Rejection rate, and Rule Hit rate.
- **Visual Analytics:** Chart.js doughnut and bar charts for verdict distributions, concept tag distributions, and failure breakdowns.
- **4-Way Case Diff Viewer:** Compares Raw Show Output $\leftrightarrow$ Rule Engine Finding $\leftrightarrow$ AI Diagnosis $\leftrightarrow$ Human Review Decision.
- **Responsible AI Inspector:** Dedicated tab exploring all 6 failure post-mortems.

---

##  Quick Start & Execution Guide

### Option 1: 1-Click Batch Runner (Windows)
Double-click `demo/run_demo.bat` or run:
```cmd
cd demo
run_demo.bat
```

### Option 2: Step-by-Step CLI Execution
```powershell
# 1. Run Deterministic Rule Checker
python checker/rule_checker.py --all --save-sample

# 2. Run AI Diagnostic Pipeline
python pipeline/run_diagnosis.py --simulate

# 3. Aggregate Performance Metrics
python dashboard/dashboard.py

# 4. Open the Web Dashboard
Start-Process dashboard/index.html
```

---

##  Evaluation Rubric Compliance Matrix

| Brief Deliverable | Expected Artifact | Location in Repository | Status |
|---|---|---|---|
| **30+ Case Dataset** | `cases.csv` + `schema.md` | `data/cases.csv`, `data/schema.md` | ✅ **32 Cases** |
| **CLI Evidence** | Synthetically generated Cisco IOS-style evidence | `data/raw_evidence/case_001_*.txt` to `case_032_*.txt` | ✅ **32 Files** |
| **Structured Prompt** | Evidence-enforced JSON prompt | `prompts/diagnose_prompt.md` | ✅ **Prompt v2.0** |
| **Few-Shot Examples** | Multi-domain worked examples | `prompts/few_shot_examples.md` | ✅ **3 Domains** |
| **Prompt Versions** | Version history & changelog | `prompts/prompt_versions/` | ✅ **v1.0, v1.1, Changelog** |
| **Deterministic Checker** | Independent rule engine + sample | `checker/rule_checker.py`, `checker/sample_output.txt` | ✅ **8 Modules (90.6% Hit)** |
| **Diagnosis Pipeline** | Batch runner + raw JSON files | `pipeline/run_diagnosis.py`, `pipeline/responses/` | ✅ **32 Responses** |
| **HITL Review Log** | Log with Accepted/Edited/Rejected | `review/review_log.csv` | ✅ **32 Audited Rows** |
| **Responsible AI Log** | Writeup of $\ge 5$ corrected cases | `review/responsible_ai_log.md` | ✅ **6 Case Studies** |
| **Analytics Dashboard** | Live metrics & case diff viewer | `dashboard/index.html`, `dashboard/dashboard.py` | ✅ **Web + CLI** |
| **Demo Script** | 5–10 min presentation script | `demo/demo_script.md`, `demo/run_demo.bat` | ✅ **Complete** |

---
## Author 
* Vishal Mansuriya
* Jyoti Basu
