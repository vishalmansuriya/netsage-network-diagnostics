"""
NetSage AI - Analytics and Metrics Aggregator
Calculates dataset distributions, AI vs Human agreement rates, error breakdowns,
and generates summary reporting for the project dashboard.
"""
import os
import sys
import csv
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

def compute_metrics():
    cases_path = os.path.join(BASE_DIR, "data", "cases.csv")
    review_path = os.path.join(BASE_DIR, "review", "review_log.csv")
    
    cases = []
    with open(cases_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cases.append(row)
            
    reviews = []
    with open(review_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reviews.append(row)
            
    total_cases = len(cases)
    
    # Concept Tag distribution
    tag_counts = {}
    for c in cases:
        tag = c.get("concept_tag", "Unknown")
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
    # Severity distribution
    sev_counts = {}
    for c in cases:
        sev = c.get("severity", "Unknown")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
        
    # OSI Layer distribution
    layer_counts = {}
    for c in cases:
        layer = f"Layer {c.get('osi_layer', '?')}"
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
        
    # Verdict counts
    verdict_counts = {"Accepted": 0, "Edited": 0, "Rejected": 0}
    for r in reviews:
        v = r.get("human_verdict", "Unknown")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
        
    # Failure breakdown by concept tag
    failure_by_tag = {}
    for r in reviews:
        if r.get("human_verdict") in ["Edited", "Rejected"]:
            tag = r.get("concept_tag", "Unknown")
            failure_by_tag[tag] = failure_by_tag.get(tag, 0) + 1
            
    # Deterministic rule agreement
    flagged_rules = sum(1 for r in reviews if r.get("rule_checker_verdict") == "FLAGGED")
    
    agreement_rate = (verdict_counts["Accepted"] / total_cases) * 100 if total_cases > 0 else 0
    edit_rate = (verdict_counts["Edited"] / total_cases) * 100 if total_cases > 0 else 0
    reject_rate = (verdict_counts["Rejected"] / total_cases) * 100 if total_cases > 0 else 0
    rule_rate = (flagged_rules / total_cases) * 100 if total_cases > 0 else 0
    
    return {
        "total_cases": total_cases,
        "agreement_rate": round(agreement_rate, 1),
        "edit_rate": round(edit_rate, 1),
        "reject_rate": round(reject_rate, 1),
        "rule_detection_rate": round(rule_rate, 1),
        "verdicts": verdict_counts,
        "tag_distribution": tag_counts,
        "severity_distribution": sev_counts,
        "layer_distribution": layer_counts,
        "failures_by_tag": failure_by_tag
    }

def print_summary(metrics):
    print("=" * 80)
    print("NETSAGE AI — PERFORMANCE & HUMAN-IN-THE-LOOP METRICS SUMMARY")
    print("=" * 80)
    print(f"Total Evaluated Cases      : {metrics['total_cases']}")
    print(f"AI Acceptance Rate         : {metrics['agreement_rate']}% ({metrics['verdicts']['Accepted']}/{metrics['total_cases']})")
    print(f"Human Edited Rate          : {metrics['edit_rate']}% ({metrics['verdicts']['Edited']}/{metrics['total_cases']})")
    print(f"Human Rejected Rate        : {metrics['reject_rate']}% ({metrics['verdicts']['Rejected']}/{metrics['total_cases']})")
    print(f"Deterministic Rule Hit Rate: {metrics['rule_detection_rate']}%")
    print("-" * 80)
    print("Case Count by Concept Tag:")
    for tag, cnt in sorted(metrics['tag_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {tag:<15}: {cnt} cases ({cnt/metrics['total_cases']*100:.1f}%)")
    print("-" * 80)
    print("Failure & Correction Breakdown by Concept Domain:")
    for tag, cnt in sorted(metrics['failures_by_tag'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {tag:<15}: {cnt} human corrections")
    print("=" * 80)

def main():
    metrics = compute_metrics()
    print_summary(metrics)
    
    # Save metrics JSON for the web dashboard
    metrics_json_path = os.path.join(CURRENT_DIR, "metrics.json")
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"[Dashboard Data Saved] metrics.json generated at {metrics_json_path}")

if __name__ == "__main__":
    main()
