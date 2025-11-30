"""Debug script to analyze prophylaxis tagging for case_highest_1 and case_highest_2."""
import json
import os
import sys

# Add rule_tagger_lichessbot to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rule_tagger_lichessbot'))

from codex_utils import analyze_position

def debug_case(case_id, fen, move):
    """Analyze a single test case and print detailed diagnostics."""
    print(f"\n{'='*80}")
    print(f"Analyzing {case_id}")
    print(f"{'='*80}")
    print(f"FEN: {fen}")
    print(f"Move: {move}")
    print()

    # Run analysis with use_new=False (legacy pipeline)
    result = analyze_position(fen, move, use_new=False)

    # Extract key information
    tags_primary = result['tags']['primary']
    prophylaxis_quality = result['tags'].get('prophylaxis_quality')
    engine_meta = result.get('engine_meta', {})

    print(f"Tags (primary): {tags_primary}")
    print(f"Prophylaxis quality: {prophylaxis_quality}")
    print()

    # Extract prophylaxis telemetry
    prophylaxis_meta = engine_meta.get('prophylaxis', {})
    print("Prophylaxis Telemetry:")
    print(f"  preventive_score: {prophylaxis_meta.get('preventive_score', 'N/A')}")
    print(f"  effective_delta: {prophylaxis_meta.get('effective_delta', 'N/A')}")
    print(f"  threat_delta: {prophylaxis_meta.get('threat_delta', 'N/A')}")
    print(f"  soft_weight: {prophylaxis_meta.get('soft_weight', 'N/A')}")
    print(f"  tactical_weight: {result.get('tactical_weight', 'N/A')}")
    print(f"  quality: {prophylaxis_meta.get('quality', 'N/A')}")
    print(f"  score: {prophylaxis_meta.get('score', 'N/A')}")
    print()

    # Extract control dynamics context
    control_dynamics = engine_meta.get('control_dynamics', {})
    context = control_dynamics.get('context', {})
    print("Control Dynamics Context:")
    print(f"  volatility_drop_cp: {context.get('volatility_drop_cp', 'N/A')}")
    print(f"  volatility_delta: {context.get('volatility_delta', 'N/A')}")
    print(f"  opp_mobility_drop: {context.get('opp_mobility_drop', 'N/A')}")
    print(f"  tension_delta: {context.get('tension_delta', 'N/A')}")
    print()

    # Extract eval information
    eval_info = result.get('eval', {})
    print("Evaluation:")
    print(f"  eval_before: {eval_info.get('before', 'N/A')}")
    print(f"  eval_played: {eval_info.get('played', 'N/A')}")
    print(f"  eval_best: {eval_info.get('best', 'N/A')}")
    print(f"  delta: {eval_info.get('delta', 'N/A')}")
    print(f"  drop_cp: {engine_meta.get('drop_cp', 'N/A')}")
    print()

    # Check failed prophylactic diagnostics
    prophylaxis_diagnostics = engine_meta.get('analysis_context', {}).get('prophylaxis_diagnostics', {})
    failure_check = prophylaxis_diagnostics.get('failure_check', {})
    if failure_check:
        print("Failed Prophylactic Check:")
        print(f"  failure_detected: {failure_check.get('failure_detected', 'N/A')}")
        print(f"  worst_eval_drop_cp: {failure_check.get('worst_eval_drop_cp', 'N/A')}")
        print(f"  threshold_cp: {failure_check.get('threshold_cp', 'N/A')}")
        print(f"  topn_checked: {failure_check.get('topn_checked', 'N/A')}")
        print(f"  failing_move_uci: {failure_check.get('failing_move_uci', 'N/A')}")
        print()

    # Extract gating information
    gating_info = engine_meta.get('gating', {})
    print("Gating Information:")
    print(f"  reason: {gating_info.get('reason', 'N/A')}")
    print(f"  tags_primary: {gating_info.get('tags_primary', 'N/A')}")
    print()

    # Check if prophylactic_move flag is set
    analysis_context = result.get('analysis_context', {})
    print("Analysis Context Flags:")
    print(f"  prophylactic_move: {analysis_context.get('prophylactic_move', 'N/A')}")
    print(f"  has_prophylaxis: {prophylaxis_meta.get('has_prophylaxis', 'N/A')}")
    print()

    return result

def main():
    """Run debug analysis on the two failing cases."""
    # Load test cases
    test_file = os.path.join(
        os.path.dirname(__file__),
        'rule_tagger_lichessbot/tests/golden_cases/cases_highest_priority.json'
    )

    with open(test_file, 'r') as f:
        cases = json.load(f)

    # Find case_highest_1 and case_highest_2
    case1 = next(c for c in cases if c['id'] == 'case_highest_1')
    case2 = next(c for c in cases if c['id'] == 'case_highest_2')

    # Debug both cases
    result1 = debug_case(
        case1['id'],
        case1['fen'],
        case1['move']
    )

    result2 = debug_case(
        case2['id'],
        case2['fen'],
        case2['move']
    )

    # Summary comparison
    print(f"\n{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}")

    print("\ncase_highest_1:")
    print(f"  Expected: {case1['expected_tags']}")
    print(f"  Current:  {case1['current_tags']}")
    print(f"  Actual:   {result1['tags']['primary']}")

    print("\ncase_highest_2:")
    print(f"  Expected: {case2['expected_tags']}")
    print(f"  Current:  {case2['current_tags']}")
    print(f"  Actual:   {result2['tags']['primary']}")

if __name__ == '__main__':
    main()
