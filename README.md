# NetSage AI

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776ab.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

> NetSage AI is a learning project for testing structured network-fault diagnoses against synthetic Cisco IOS-style evidence. It combines deterministic checks, a JSON diagnostic pipeline, and a comparison log.

---

##  Table of Contents

- [Overview](#-overview)
- [System Architecture & Workflow](#-system-architecture--workflow)
- [Repository Structure](#-repository-structure)
- [Dataset & OSI Layer Coverage](#-dataset--osi-layer-coverage)
- [Deterministic Rule Checker Engine](#-deterministic-rule-checker-engine)
- [Prompt Engineering & Evidence Grounding](#-prompt-engineering--evidence-grounding)
- [Pipeline Re-execution & Responsible AI](#-pipeline-re-execution--responsible-ai)
- [Interactive Analytics Web Dashboard](#-interactive-analytics-web-dashboard)
- [Quick Start & Execution Guide](#-quick-start--execution-guide)
- [Evaluation Rubric Compliance Matrix](#-evaluation-rubric-compliance-matrix)
- [Team & Contributions](#-team--contributions)

---

## Overview

The repository contains a synthetic benchmark and a small diagnostic pipeline.

1. **Deterministic rule checker:** evaluates conditions such as subnet boundaries, duplicate IPs, gateways, VLANs, MTU, and ACLs.
2. **Structured diagnostic prompt:** requests evidence-backed JSON diagnoses from the pipeline.
3. **Re-execution comparison:** compares the emitted `root_cause` with each case's `expected_fault`. The current rerun is 32 Accepted, 0 Edited, and 0 Rejected.

---

##  System Architecture & Workflow

```
+-------------------------------------------------------------------------+
|                  32+ Cisco IOS Incident Cases (data/cases.csv)          |
|            Synthetic CLI Captures (data/raw_evidence/)                 |
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
|              Re-execution Comparison (review/review_log.csv)            |
|                  Verdict: Accepted / Edited / Rejected                  |
+------------------------------------+------------------------------------+
                                     |
                    +----------------+----------------+
                    |                                 |
                    v                                 v
    +---------------+---------------+ +---------------+---------------+
    |  Six Rerun Evidence Records  | |  Interactive Web Dashboard    |
    | (review/responsible_ai_log.md)| |  (Charts & Case Diff)         |
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
│   ├── review_log.csv                 # 32-row comparison log (Accepted: 100.0%, Edited: 0.0%, Rejected: 0.0%)
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

The dataset contains **32 synthetically generated, internally consistent cases, validated for topology/IP/VLAN coherence.** They use Cisco IOS-style CLI syntax. `scripts/build_data.py` is the data source: it materializes `data/cases.csv` and the 32 files in `data/raw_evidence/`; the evidence files are synthetically generated CLI-style captures, not captures from live network devices.

| Concept Tag | Case Count | % of Dataset | Tested Scenarios |
|---|---|---|---|
| **Routing** | 7 | 21.9% | OSPF MTU Mismatch, Missing Default Route, Passive Interface, BGP AS Mismatch, Recursive Lookup Failure, Subnet Mask Mismatch, Default Gateway Mismatch |
| **Wireless / L2** | 6 | 18.8% | BPDU Guard Err-Disable, Duplex Mismatch Late Collisions, Port Security Violation, ARP Spoofing / DAI, STP Root Guard Block, CAPWAP Tunnel ACL Drop |
| **DHCP** | 5 | 15.6% | DHCP Relay Helper Missing, Scope Pool Exhaustion, Rogue DHCP Server, Duplicate IP Conflict, Gateway IP Lease Hijacking |
| **NAT / PAT** | 4 | 12.5% | Inside/Outside Interface Inversion, Overload ACL Subnet Mismatch, Pool Overlap with ISP Gateway, Static NAT DNS Typo |
| **ACL / Security** | 4 | 12.5% | Inter-VLAN Standard ACL Drop, Missing TCP Established Keyword, DNS UDP 53 vs TCP 53 Typo, ACL Applied on Wrong Interface |
| **VLAN / Trunking** | 3 | 9.4% | 802.1Q Native VLAN Mismatch, Access Port in Non-Existent VLAN, Trunk Allowed List Pruned Critical VLAN |
| **DNS Resolution** | 3 | 9.4% | Decommissioned Primary DNS IP, Split-Brain Forwarder Misconfiguration, Path MTU IPsec Tunnel Blackhole |

### Case diversity

No near-duplicate cases were found. Within each concept tag, the cases use different underlying fault mechanisms rather than the same fault with only IP addresses, hostnames, or interfaces changed.

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

## Pipeline Re-execution & Responsible AI

The pipeline was rerun across all 32 cases and each emitted `root_cause` was compared with `data/cases.csv`'s `expected_fault`. The current client labels every output `engine_mode: simulation`; these are comparison results for the embedded response map, not a hosted-model evaluation or a human-review study.

```
================================================================================
NETSAGE AI — PERFORMANCE & HUMAN-IN-THE-LOOP METRICS SUMMARY
================================================================================
Total Evaluated Cases      : 32
Root-Cause Agreement Rate  : 100.0% (32/32 cases)
Comparison Edited Rate     : 0.0% (0/32 cases)
Comparison Rejected Rate   : 0.0% (0/32 cases)
Deterministic Rule Hit Rate: 90.6% (29/32 cases caught deterministically)
================================================================================
```

### Rerun evidence records in `review/responsible_ai_log.md`

The rerun records CASE-007, CASE-012, CASE-018, CASE-026, CASE-015, and CASE-020. Each emitted root cause matches its corresponding expected fault; none diverged in this execution.

---

##  Interactive Analytics Web Dashboard

The web dashboard (`dashboard/index.html`) provides:

- metrics cards for case count, comparison verdicts, and rule hits;
- charts for verdict and concept-tag distributions;
- a case view with evidence, rule-check, diagnosis, and comparison details; and
- a tab for the six rerun evidence records.

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
| **Comparison Log** | Log with Accepted/Edited/Rejected | `review/review_log.csv` | ✅ **32 Re-executed Rows** |
| **Rerun Evidence Log** | Response/ground-truth comparison | `review/responsible_ai_log.md` | ✅ **6 Case Records** |
| **Analytics Dashboard** | Live metrics & case diff viewer | `dashboard/index.html`, `dashboard/dashboard.py` | ✅ **Web + CLI** |
| **Demo Script** | 5–10 min presentation script | `demo/demo_script.md`, `demo/run_demo.bat` | ✅ **Complete** |

---
## Author 
* Vishal Mansuriya
* Jyoti Basu
