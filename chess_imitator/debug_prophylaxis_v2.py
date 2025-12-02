"""Enhanced debug script with more prophylaxis details."""
import json
import os
import sys

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

    result = analyze_position(fen, move, use_new=False)

    tags_primary = result['tags']['primary']
    tags_all = result['tags']['all']

    print(f"Tags (primary): {tags_primary}")
    print()

    # Get full engine_meta for deep inspection
    engine_meta = result.get('engine_meta', {})
    analysis_context = result.get('analysis_context', {})

    # Check if prophylactic_move flag is set in metadata
    print(f"prophylactic_move flag in context: {analysis_context.get('prophylactic_move', False)}")
    print(f"prophylactic_move flag in tags_all: {tags_all.get('prophylactic_move', False)}")
    print()

    # Detailed prophylaxis metadata
    prophylaxis_meta = engine_meta.get('prophylaxis', {})
    print("Prophylaxis Metadata:")
    for key, value in prophylaxis_meta.items():
        if key == 'telemetry' or key == 'components':
            print(f"  {key}:")
            for k, v in (value or {}).items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    print()

    # Failed prophylactic check
    prophylaxis_diagnostics = analysis_context.get('prophylaxis_diagnostics', {})
    failure_check = prophylaxis_diagnostics.get('failure_check', {})
    if failure_check:
        print("Failed Prophylactic Check:")
        for key, value in failure_check.items():
            print(f"  {key}: {value}")
        print()
    else:
        print("Failed Prophylactic Check: NOT RUN (prophylactic_move flag may be False)")
        print()

    # Eval info
    eval_info = result.get('eval', {})
    print(f"Eval before (cp): {int(eval_info.get('before', 0) * 100)}")
    print(f"Eval played (cp): {int(eval_info.get('played', 0) * 100)}")
    print(f"Eval drop (cp): {int(eval_info.get('before', 0) * 100) - int(eval_info.get('played', 0) * 100)}")
    print()

    return result

def main():
    """Run debug analysis on the two failing cases."""
    test_file = os.path.join(
        os.path.dirname(__file__),
        'rule_tagger_lichessbot/tests/golden_cases/cases_highest_priority.json'
    )

    with open(test_file, 'r') as f:
        cases = json.load(f)

    case1 = next(c for c in cases if c['id'] == 'case_highest_1')
    case2 = next(c for c in cases if c['id'] == 'case_highest_2')

    result1 = debug_case(case1['id'], case1['fen'], case1['move'])
    result2 = debug_case(case2['id'], case2['fen'], case2['move'])

    print(f"\n{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}")

    print("\ncase_highest_1:")
    print(f"  Expected: {case1['expected_tags']}")
    print(f"  Actual:   {result1['tags']['primary']}")
    missing1 = set(case1['expected_tags']) - set(result1['tags']['primary'])
    extra1 = set(result1['tags']['primary']) - set(case1['expected_tags'])
    if missing1:
        print(f"  Missing:  {list(missing1)}")
    if extra1:
        print(f"  Extra:    {list(extra1)}")

    print("\ncase_highest_2:")
    print(f"  Expected: {case2['expected_tags']}")
    print(f"  Actual:   {result2['tags']['primary']}")
    missing2 = set(case2['expected_tags']) - set(result2['tags']['primary'])
    extra2 = set(result2['tags']['primary']) - set(case2['expected_tags'])
    if missing2:
        print(f"  Missing:  {list(missing2)}")
    if extra2:
        print(f"  Extra:    {list(extra2)}")

if __name__ == '__main__':
    main()
