"""
NetSage AI - Deterministic Rule Checker Engine
Executes deterministic, non-AI rule validations across network incident cases to establish ground truth
and verify LLM diagnoses before and after inference.
"""
import os
import sys
import csv
import json
import argparse

# Add parent directory to sys.path to allow module imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, CURRENT_DIR)

from rules.duplicate_ip import check_duplicate_ip
from rules.mask_mismatch import check_mask_mismatch
from rules.gateway_mismatch import check_gateway_mismatch
from rules.interface_down import check_interface_down
from rules.missing_vlan import check_missing_vlan
from rules.missing_route import check_missing_route
from rules.acl_deny_implicit import check_acl_deny
from rules.nat_overload_pool import check_nat_rules

ALL_RULES = [
    check_duplicate_ip,
    check_mask_mismatch,
    check_gateway_mismatch,
    check_interface_down,
    check_missing_vlan,
    check_missing_route,
    check_acl_deny,
    check_nat_rules
]

def run_case_rules(case):
    """
    Evaluates all registered deterministic rules against a single case dictionary.
    Returns aggregated evaluation dictionary.
    """
    violations = []
    passes = []
    
    for rule_fn in ALL_RULES:
        try:
            res = rule_fn(case)
            if res.get("status") == "VIOLATION":
                violations.append(res)
            elif res.get("status") == "PASS":
                passes.append(res)
        except Exception as e:
            violations.append({
                "rule": rule_fn.__name__,
                "status": "ERROR",
                "finding": f"Exception executing rule: {str(e)}"
            })
            
    has_violation = len(violations) > 0
    primary_finding = violations[0]["finding"] if has_violation else "All deterministic rules passed."
    evidence = violations[0].get("evidence", "N/A") if has_violation else "N/A"
    
    return {
        "case_id": case.get("case_id", "UNKNOWN"),
        "verdict": "FLAGGED" if has_violation else "CLEAN",
        "violations_count": len(violations),
        "primary_violation": primary_finding,
        "evidence": evidence,
        "all_violations": violations,
        "rules_evaluated": len(ALL_RULES)
    }

def run_dataset_rules(cases_path=None):
    """
    Runs the deterministic rule engine over all cases in cases.csv.
    """
    if cases_path is None:
        cases_path = os.path.join(BASE_DIR, "data", "cases.csv")
        
    results = []
    with open(cases_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            res = run_case_rules(row)
            res["expected_fault"] = row.get("expected_fault")
            res["concept_tag"] = row.get("concept_tag")
            res["osi_layer"] = row.get("osi_layer")
            results.append(res)
            
    return results

def format_console_report(results):
    """
    Formats rule checker results into a clean, human-readable terminal report.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("NETSAGE AI — DETERMINISTIC RULE CHECKER ENGINE REPORT")
    lines.append("=" * 80)
    lines.append(f"{'Case ID':<10} | {'Tag':<12} | {'Layer':<6} | {'Verdict':<8} | {'Primary Deterministic Finding'}")
    lines.append("-" * 80)
    
    flagged_count = 0
    clean_count = 0
    
    for r in results:
        v = r["verdict"]
        if v == "FLAGGED":
            flagged_count += 1
        else:
            clean_count += 1
        desc = (r["primary_violation"][:42] + "...") if len(r["primary_violation"]) > 42 else r["primary_violation"]
        lines.append(f"{r['case_id']:<10} | {r['concept_tag']:<12} | L{r['osi_layer']:<5} | {v:<8} | {desc}")
        
    lines.append("=" * 80)
    lines.append(f"Summary: {len(results)} Cases Evaluated | {flagged_count} Flagged Violations | {clean_count} Clean Passes")
    lines.append(f"Detection Rate: {(flagged_count/len(results))*100:.1f}%")
    lines.append("=" * 80)
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="NetSage AI Deterministic Rule Checker")
    parser.add_argument("--case", type=str, help="Specific Case ID to evaluate (e.g. CASE-001)")
    parser.add_argument("--all", action="store_true", help="Run across all 30+ cases in data/cases.csv")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--save-sample", action="store_true", help="Save output to checker/sample_output.txt")
    
    args = parser.parse_args()
    
    cases_path = os.path.join(BASE_DIR, "data", "cases.csv")
    results = run_dataset_rules(cases_path)
    
    if args.case:
        filtered = [r for r in results if r["case_id"] == args.case]
        if not filtered:
            print(f"Case {args.case} not found.")
            return
        if args.json:
            print(json.dumps(filtered[0], indent=2))
        else:
            print(json.dumps(filtered[0], indent=2))
        return
        
    report = format_console_report(results)
    print(report)
    
    # Save sample_output.txt deliverable
    sample_file = os.path.join(CURRENT_DIR, "sample_output.txt")
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(report)
        f.write("\n\n" + "=" * 80 + "\nDETAILED RULE TRACE (FIRST 3 CASES)\n" + "=" * 80 + "\n")
        for r in results[:3]:
            f.write(json.dumps(r, indent=2) + "\n\n")
    print(f"\n[Artifact Saved] sample_output.txt updated at {sample_file}")

if __name__ == "__main__":
    main()
