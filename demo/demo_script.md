# NetSage AI — 5–10 Minute Demo Video Script & Shot List

**Project:** NetSage AI (Applied AI + Network Troubleshooting)  
**Presenter:** Sanjay (Lead Presenter & Network AI Engineer)  
**Target Duration:** 8 minutes (Flexible: 5–10 minutes)  
**Screen Setup:** Split-screen with Terminal (VS Code / PowerShell) on the left and NetSage AI Interactive Dashboard on the right.

---

## Shot List & Time Breakdown

```
[0:00 - 1:00]  Scene 1: Introduction & The Core Problem
[1:00 - 2:30]  Scene 2: Data Architecture & Cisco Evidence Fidelity
[2:30 - 4:00]  Scene 3: Deterministic Rule Checker Live Execution
[4:00 - 5:30]  Scene 4: AI Diagnosis Pipeline & Structured JSON Schema
[5:30 - 7:15]  Scene 5: Human-in-the-Loop Audit & Broken Case Deep-Dive
[7:15 - 8:30]  Scene 6: Analytics Dashboard & System Metrics
[8:30 - 9:15]  Scene 7: Key Learnings & Conclusion
```

---

## Scene 1: Introduction & The Core Problem (0:00 – 1:00)
- **Visual:** NetSage AI Dashboard Overview (`dashboard/index.html`) on screen.
- **Presenter Talking Points:**
  > "Hello everyone! Welcome to our demonstration of **NetSage AI**, an applied AI network diagnostic platform developed for the Cisco Internship (Project 2).
  >
  > In enterprise networks, applying generative AI directly to production routers without governance is dangerous. Large language models frequently hallucinate root causes, misdiagnose multi-layer anomalies, or propose destructive commands.
  >
  > NetSage AI solves this through a **dual-layer architecture**: combining independent **deterministic rule checking** with **evidence-grounded LLM inference**, governed by mandatory **Human-in-the-Loop (HITL) review**. Every single diagnosis produces an auditable review record before changes are accepted."

---

## Scene 2: Data Architecture & Cisco Evidence Fidelity (1:00 – 2:30)
- **Visual:** Open `data/cases.csv` and show sample evidence files in `data/raw_evidence/` (e.g. `case_001_show_output.txt` and `case_007_show_output.txt`).
- **Presenter Talking Points:**
  > "To ensure rigorous evaluation, we developed a benchmark of **32 synthetically generated, internally consistent cases, validated for topology/IP/VLAN coherence** across all 7 OSI layers.
  >
  > Rather than using generic descriptions, our `data/raw_evidence/` folder contains realistic Cisco IOS CLI outputs—including `show ip route`, `show ip interface brief`, `show interfaces trunk`, `show access-lists`, and `show ip nat translations`.
  >
  > We ensured strict internal consistency: IP addresses, subnet masks, interface names, and MAC addresses align 100% between the topology notes and show command captures. Our dataset is evenly balanced across 7 concept tags: VLANs, Routing (OSPF/BGP), NAT, DHCP, ACLs, DNS, and Wireless/Layer 2 security."

---

## Scene 3: Deterministic Rule Checker Live Execution (2:30 – 4:00)
- **Visual:** Switch to Terminal and run: `python checker/rule_checker.py --all`
- **Presenter Talking Points:**
  > "Now, let's run our **deterministic rule checker**. This engine runs completely independently of the AI and serves as our non-negotiable ground truth.
  >
  > It executes 8 modular rule plugins: detecting duplicate IP addresses, subnet mask boundary misalignments, default gateways in foreign subnets, err-disabled ports, missing VLAN database entries, routing table reachability, and ACL filter drops.
  >
  > As you see on screen, the rule checker evaluated all 32 cases in milliseconds, catching 29 violations with a **90.6% deterministic detection rate**. We run this both before AI diagnosis to validate the test case, and after inference to score the AI's answer against deterministic logic."

---

## Scene 4: AI Diagnosis Pipeline & Structured JSON Schema (4:00 – 5:30)
- **Visual:** Show `prompts/diagnose_prompt.md` and execute: `python pipeline/run_diagnosis.py --simulate`
- **Presenter Talking Points:**
  > "Next is the **AI Diagnosis Pipeline**. We engineered a strict prompt in `prompts/diagnose_prompt.md` enforcing JSON schema output with mandatory evidence grounding.
  >
  > The model is strictly instructed: it cannot assign 'high' confidence unless it quotes exact lines or parameters from the Cisco show output in its `evidence` field.
  >
  > Running `run_diagnosis.py` processes each case, validates the schema, checks evidence citations, and persists raw responses to `pipeline/responses/`. Notice how every response includes root cause, OSI layer, confidence, next verification command, and ordered Cisco CLI fix steps."

---

## Scene 5: Human-in-the-Loop Audit & Broken Case Deep-Dive (5:30 – 7:15)
- **Visual:** Open Dashboard 'Responsible AI Audit' tab and 'Case Explorer' modal for `CASE-007` and `CASE-012`.
- **Presenter Talking Points:**
  > "The current `review_log.csv` records a pipeline re-execution comparison. We ran all 32 cases and compared each emitted `root_cause` with the expected fault: **Accepted (100.0%)**, **Edited (0.0%)**, and **Rejected (0.0%)**.
  >
  > Let's look at **Case 007 (OSPF Adjacency Stuck in EXSTART)**. The executed response identifies the MTU mismatch between R1 (1500) and R2 (1400), matching the expected diagnosis.
  >
  > In **Case 012 (NAT Inversion)**, the executed response identifies the inverted `ip nat inside/outside` tags on the LAN/WAN interfaces. The six rerun records are in `review/responsible_ai_log.md`. The current client uses embedded simulation responses, not a hosted-model API."

---

## Scene 6: Analytics Dashboard & System Metrics (7:15 – 8:30)
- **Visual:** Walk through the live charts and interactive table in `dashboard/index.html`.
- **Presenter Talking Points:**
  > "Let's explore our **interactive analytics dashboard**.
  >
  > On the KPI bar, we track 32 cases, 100.0% root-cause agreement in the re-execution comparison, 0.0% edited, 0.0% rejected, and a 90.6% rule detection rate.
  >
  > The charts visualize comparison verdicts, OSI layer breakdown, and concept tag distribution. The current re-execution has no edited or rejected comparison rows.
  >
  > In the Case Explorer, we can filter by concept tag, search symptoms, and click 'Inspect' on any case to see a 4-way side-by-side comparison between Raw Evidence, Rule Checker, AI Diagnosis, and Human Reviewer Edits."

---

## Scene 7: Key Learnings & Conclusion (8:30 – 9:15)
- **Visual:** NetSage AI Architecture Overview slide / tab.
- **Presenter Talking Points:**
  > "In conclusion, NetSage AI demonstrates that building trustworthy AI for critical infrastructure requires more than prompt engineering—it demands **deterministic ground truth validation**, **evidence-grounded guardrails**, and **human-in-the-loop accountability**.
  >
  > All deliverables—from our 32-case dataset, prompt changelog, and rule engine to our review logs, dashboard, and RAI writeup—are fully reproducible in our repository.
  >
  > Thank you for watching!"

---

## Recording Tips for the Team
1. **Resolution:** Record at 1080p (1920x1080) with 125% browser zoom for crisp text readability.
2. **Audio:** Use a dedicated microphone; speak at a deliberate, confident pace.
3. **Live Demonstration:** Keep the terminal command output visible when running `rule_checker.py` to prove real execution.
