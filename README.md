# NetSage AI

A Python-based network troubleshooting project that combines a deterministic rule checker, an AI-assisted diagnosis pipeline, and human review logging for Cisco-style incident cases.

## Project goal

This repository is designed to explore a practical pattern for network diagnosis:

- Use deterministic checks to identify objective network faults from Cisco-style `show` output.
- Feed that evidence into a structured AI diagnosis workflow.
- Validate the AI output against a rule-based baseline.
- Record human review decisions to create an audit trail.

The project is built around synthetic but realistic network incident data and is meant for experimentation, benchmarking, and demonstration.

## What is in this repo

- `data/` contains the case dataset and raw Cisco show-output evidence.
- `checker/` contains the deterministic rule engine and modular checks.
- `pipeline/` contains the diagnosis orchestration and simulated AI client.
- `review/` contains the human review log and responsible-AI notes.
- `dashboard/` contains the metrics generator and a small HTML dashboard.
- `prompts/` contains the prompt used for AI diagnosis.
- `demo/` contains the local demo script and launcher.

## Architecture

The repo follows a simple three-stage workflow:

1. Rule-based validation
   - The checker reads each case and evaluates deterministic conditions such as:
     - VLAN mismatch
     - missing default route
     - bad gateway
     - duplicate IP
     - NAT misconfiguration
     - ACL problems
     - OSPF/BGP issues

2. AI diagnosis
   - The pipeline loads a case, runs the rule checker, and sends the evidence to the AI client.
   - The AI response is expected to return structured JSON with fields such as:
     - `case_id`
     - `root_cause`
     - `osi_layer`
     - `confidence`
     - `evidence`
     - `next_command`
     - `fix_steps`

3. Human review
   - The project keeps a review log with verdicts like `Accepted`, `Edited`, and `Rejected`.
   - That creates a lightweight HITL audit process and supports post-mortem analysis.

## Repository structure

```text
ciscovip/
├── README.md
├── checker/
│   ├── rule_checker.py
│   ├── sample_output.txt
│   └── rules/
│       ├── acl_deny_implicit.py
│       ├── duplicate_ip.py
│       ├── gateway_mismatch.py
│       ├── interface_down.py
│       ├── mask_mismatch.py
│       ├── missing_route.py
│       ├── missing_vlan.py
│       └── nat_overload_pool.py
├── dashboard/
│   ├── app.js
│   ├── dashboard.py
│   ├── index.html
│   ├── metrics.json
│   └── styles.css
├── data/
│   ├── cases.csv
│   ├── raw_evidence/
│   └── schema.md
├── demo/
│   ├── demo_script.md
│   └── run_demo.bat
├── pipeline/
│   ├── ai_client.py
│   ├── responses/
│   └── run_diagnosis.py
├── prompts/
│   ├── diagnose_prompt.md
│   ├── few_shot_examples.md
│   └── prompt_versions/
├── review/
│   ├── responsible_ai_log.md
│   └── review_log.csv
├── scripts/
│   └── build_data.py
└──
```

## Data set

The project includes a synthetic but internally consistent set of Cisco networking incident cases in `data/cases.csv`.

Each row contains:

- `case_id`
- `symptom`
- `topology_note`
- `show_output`
- `expected_fault`
- `osi_layer`
- `concept_tag`
- `severity`
- `evidence_file`

The raw evidence files in `data/raw_evidence/` provide Cisco-style command output used for diagnosis.

## Verified project behavior

The following commands were run successfully in this workspace to validate the repo:

```bash
python checker/rule_checker.py --all --save-sample
python dashboard/dashboard.py
python pipeline/run_diagnosis.py --simulate
```

Observed results from the verified run:

- `32` cases evaluated
- `29` cases flagged by the deterministic rule engine
- `3` cases passed without rule violations
- rule detection rate: `90.6%`
- pipeline completed successfully and generated responses under `pipeline/responses/`

## Quick start

From the project root:

```bash
# 1) Run the deterministic rule checker
python checker/rule_checker.py --all --save-sample

# 2) Run the AI diagnosis simulation
python pipeline/run_diagnosis.py --simulate

# 3) Generate dashboard metrics
python dashboard/dashboard.py
```

To open the dashboard locally:

- open `dashboard/index.html` in a browser, or
- on Windows, you may open it via the file explorer or an editor preview

## Notes on the AI pipeline

The simulation mode is the safe default for local runs. The project also supports a live mode path in `pipeline/ai_client.py`, but the dependable baseline here is the offline simulation mode because it does not require external API keys or network access.

The system is intentionally designed to separate:

- grounded deterministic checks
- AI-generated hypotheses
- explicit human approval or correction

That makes it useful as a demonstration of responsible AI patterns in network operations.

## How the rule checker works

`checker/rule_checker.py` loads all cases from `data/cases.csv` and evaluates a set of rule functions. Each rule returns a status such as:

- `PASS`
- `VIOLATION`
- `ERROR`

The overall result includes:

- `case_id`
- `verdict`
- `violations_count`
- `primary_violation`
- `evidence`
- `all_violations`

This is useful as an objective reference point against which the AI diagnosis can be compared.

## Review and audit trail

The review data in `review/review_log.csv` stores human verdicts for each case. The accepted/edited/rejected patterns are used to understand where the AI is correct, where it needs intervention, and where the diagnosis is materially wrong.

The repository also includes a responsible-AI writeup in `review/responsible_ai_log.md` for several failure cases.

## Practical use

This project is best viewed as a prototype for:

- AI-assisted network troubleshooting
- deterministic validation for critical systems
- human-in-the-loop operating workflows
- dataset and prompt iteration for technical diagnosis tasks

It is not a production network automation toolkit by itself; it is a focused research and demonstration project around trustworthy diagnostics.

## Suggested next steps

- Add true unit tests for the rule engine
- Add a CLI wrapper for single-case analysis
- Add a front-end filter/search for case review
- Add live LLM provider integration with schema enforcement
- Expand the dataset beyond the current synthetic cases

## License

This project is provided as-is for learning and experimentation within the repository context.

