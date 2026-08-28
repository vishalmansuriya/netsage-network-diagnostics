"""
NetSage AI - Batch Diagnostic Pipeline Orchestrator
Executes end-to-end diagnosis across all cases in data/cases.csv, invokes deterministic rule checks,
queries the AI Diagnostic Client, validates output against schema, and writes raw responses to pipeline/responses/.
"""
import os
import sys
import csv
import json
import argparse
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, CURRENT_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "checker"))

from ai_client import NetSageAIClient
from rule_checker import run_case_rules

RESPONSES_DIR = os.path.join(CURRENT_DIR, "responses")
os.makedirs(RESPONSES_DIR, exist_ok=True)

def run_pipeline(cases_csv_path=None, mode="simulation"):
    if cases_csv_path is None:
        cases_csv_path = os.path.join(BASE_DIR, "data", "cases.csv")
        
    client = NetSageAIClient(mode=mode)
    
    cases = []
    with open(cases_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cases.append(row)
            
    print(f"Starting NetSage AI Diagnosis Pipeline on {len(cases)} cases [Mode: {mode.upper()}]...")
    print("=" * 80)
    
    results_summary = []
    
    for i, case in enumerate(cases, 1):
        cid = case["case_id"]
        # Step 1: Pre-diagnosis Deterministic Check
        rule_eval = run_case_rules(case)
        
        # Step 2: AI Diagnosis
        ai_resp = client.diagnose_case(case)
        
        # Step 3: Schema Validation
        is_valid, validation_msg = client.validate_schema(ai_resp)
        ai_resp["schema_valid"] = is_valid
        ai_resp["rule_checker_verdict"] = rule_eval["verdict"]
        ai_resp["rule_checker_violation"] = rule_eval["primary_violation"]
        
        # Save individual JSON response
        num_str = cid.split("-")[1]
        out_filename = f"case_{num_str}_response.json"
        out_path = os.path.join(RESPONSES_DIR, out_filename)
        with open(out_path, "w", encoding="utf-8") as rf:
            json.dump(ai_resp, rf, indent=2)
            
        print(f"[{i:02d}/{len(cases)}] {cid:<10} | Conf: {ai_resp.get('confidence','?'):<6} | Layer: L{ai_resp.get('osi_layer','?')} | Rules: {rule_eval['verdict']:<8} -> Saved {out_filename}")
        
        results_summary.append({
            "case_id": cid,
            "concept_tag": case.get("concept_tag"),
            "severity": case.get("severity"),
            "ai_root_cause": ai_resp.get("root_cause"),
            "ai_confidence": ai_resp.get("confidence"),
            "rule_verdict": rule_eval["verdict"],
            "schema_valid": is_valid
        })
        
    print("=" * 80)
    print(f"Pipeline Execution Complete! {len(cases)} responses generated in {RESPONSES_DIR}")
    return results_summary

def main():
    parser = argparse.ArgumentParser(description="NetSage AI Batch Diagnosis Pipeline")
    parser.add_argument("--simulate", action="store_true", default=True, help="Run in offline simulation mode")
    parser.add_argument("--live", action="store_true", help="Run with live LLM API calls")
    args = parser.parse_args()
    
    mode = "live" if args.live else "simulation"
    run_pipeline(mode=mode)

if __name__ == "__main__":
    main()
