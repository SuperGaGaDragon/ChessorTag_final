"""Debug why initiative/tension tags are missing for case_highest_2."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rule_tagger_lichessbot'))

from codex_utils import analyze_position

# case_highest_2
fen = "r1b1kb1r/pppnqp2/3p1npp/2P1p3/3PP3/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 0 8"
move = "a7a6"

result = analyze_position(fen, move, use_new=False)

tag_flags = result.get('engine_meta', {}).get('tag_flags', {})
tags_primary = result['tags']['primary']

print("case_highest_2 (a7a6):")
print(f"  initiative_attempt flag: {tag_flags.get('initiative_attempt', False)}")
print(f"  tension_creation flag: {tag_flags.get('tension_creation', False)}")
print(f"  prophylactic_move flag: {tag_flags.get('prophylactic_move', False)}")
print(f"  primary tags: {tags_primary}")
print()

# Check gating
gating_info = result.get('engine_meta', {}).get('gating', {})
print(f"  gating_reason: {gating_info.get('reason')}")
print(f"  tags_before_gating (secondary): {result['tags'].get('secondary', [])}")
