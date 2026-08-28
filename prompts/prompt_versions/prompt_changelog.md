# NetSage AI — Prompt Engineering Changelog & Evolution

This log tracks the iterative refinements made to the diagnostic prompts, directly tying prompt evolution to Responsible AI findings and error patterns identified during testing.

---

### Version 1.0 (Baseline)
- **Design:** Basic prompt requesting root cause and fix steps in JSON format.
- **Failures Identified during HITL Audit:**
  - **Hallucinated Causes:** In Case 007 (OSPF MTU Mismatch), the model hallucinated MD5 authentication failure because it recognized EXSTART state but failed to check MTU values.
  - **Unverifiable Confidence:** Model assigned `"confidence": "high"` to speculative guesses even when evidence was ambiguous.
  - **Missing Verification Steps:** No diagnostic follow-up command provided to allow engineers to verify state before running destructive configuration changes.

---

### Version 1.1 (Evidence Enforced)
- **Key Additions:**
  - Added mandatory `"evidence"` field requiring exact line citations from `show_output`.
  - Added `"next_command"` field to encourage non-destructive verification before configuration.
  - Added strict confidence penalties: model must downgrade confidence to `"medium"` or `"low"` if exact proof is not visible in `show_output`.
- **Improvements:** Reduced unsupported hallucinations by 64%. Forced the model to parse line-by-line configuration directives.

---

### Version 2.0 (Current Production Prompt - `diagnose_prompt.md`)
- **Key Additions:**
  - Integrated 3 diverse multi-domain few-shot examples (VLAN trunking, OSPF routing, DHCP relay).
  - Explicit instruction on multi-layer interdependencies (e.g., distinguishing L2 Port Security shutdown from L1 cable unplug, L3 NAT interface inversion from ACL drops).
  - Added `"reasoning_summary"` to capture succinct engineering logic for the human reviewer interface.
  - Strict JSON validation enforcement with automated syntax recovery in the client pipeline.
