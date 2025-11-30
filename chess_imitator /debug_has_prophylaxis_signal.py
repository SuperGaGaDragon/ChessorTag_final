"""Debug has_prophylaxis_signal for case_highest_2."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rule_tagger_lichessbot'))

# Calculate has_prophylaxis_signal for case_highest_2
preventive_score = 0.004
signal_threshold = 0.16 * 0.85  # 0.136

print(f"case_highest_2:")
print(f"  preventive_score: {preventive_score}")
print(f"  signal_threshold: {signal_threshold}")
print(f"  prophylaxis_signal_score: {preventive_score}")
print(f"  has_prophylaxis_signal: {preventive_score >= signal_threshold}")
print()
print(f"Since has_prophylaxis_signal is False, classify_prophylaxis_quality is never called.")
print(f"We need to adjust the has_prophylaxis_signal logic to include pattern support.")
