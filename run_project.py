#!/usr/bin/env encoding=utf-8
"""
Main Execution Script for Instamart Customer Intelligence & Support Copilot.
Triggers orchestration pipelines sequentially across structural layers.
"""
import os
import sys

# Import localized step handlers
from part_a import run_part_a
from part_b import run_part_b
from part_c import run_part_c
from part_d import run_part_d

def main():
    print("======================================================================")
    print("      STARTING INSTAMART CUSTOMER INTELLIGENCE PIPELINE ENGINE        ")
    print("======================================================================")

    # Pre-flight data paths availability assurance validation check
    if not os.path.exists('data/raw/customers.csv'):
        print("[CRITICAL ERROR] Missing 'data/raw/customers.csv'. Please add raw source tables first.")
        sys.exit(1)

    try:
        # Core Execution Loop Sequence
        run_part_a()
        run_part_b()
        run_part_c()
        run_part_d()

        print("\n======================================================================")
        print(" SUCCESS: ALL CAPSTONE PIPELINE STEPS COMPLETED SUCCESSFULLY!        ")
        print(" All evaluation files are exported inside your 'outputs/' folder.     ")
        print("======================================================================")

    except Exception as err:
        print(f"\n[PIPELINE EXECUTION CRASHED]: {str(err)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
