"""Test all 8 highest_priority cases."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rule_tagger_lichessbot'))

from codex_utils import analyze_position

def test_case(case_id, fen, move, expected_tags):
    """Test a single case and return results."""
    result = analyze_position(fen, move, use_new=False)
    actual_tags = result['tags']['primary']

    expected_set = set(expected_tags)
    actual_set = set(actual_tags)

    missing = expected_set - actual_set
    extra = actual_set - expected_set
    match = (missing == set() and extra == set())

    return {
        'case_id': case_id,
        'expected': expected_tags,
        'actual': actual_tags,
        'missing': list(missing),
        'extra': list(extra),
        'match': match
    }

def main():
    """Test all highest_priority cases."""
    test_file = os.path.join(
        os.path.dirname(__file__),
        'rule_tagger_lichessbot/tests/golden_cases/cases_highest_priority.json'
    )

    with open(test_file, 'r') as f:
        cases = json.load(f)

    results = []
    perfect_count = 0

    print("Testing all highest_priority cases...\n")
    print("="*80)

    for case in cases:
        case_id = case['id']
        fen = case['fen']
        move = case.get('move_uci') or case['move']
        expected = case['expected_tags']

        result = test_case(case_id, fen, move, expected)
        results.append(result)

        status = "✅ PASS" if result['match'] else "❌ FAIL"
        print(f"\n{status} {case_id}:")
        print(f"  Expected: {result['expected']}")
        print(f"  Actual:   {result['actual']}")

        if result['missing']:
            print(f"  Missing:  {result['missing']}")
        if result['extra']:
            print(f"  Extra:    {result['extra']}")

        if result['match']:
            perfect_count += 1

    print("\n" + "="*80)
    print(f"\nSUMMARY: {perfect_count}/{len(cases)} cases pass")
    print(f"Pass rate: {perfect_count/len(cases)*100:.1f}%")

    return results

if __name__ == '__main__':
    main()
