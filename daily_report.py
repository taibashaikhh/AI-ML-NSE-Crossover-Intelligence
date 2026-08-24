"""Generate the auditable crossover/ML evaluation and optionally train next day."""
import argparse
from pprint import pprint
from learning import LearningManager

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", help="Evaluate a specific YYYY-MM-DD day")
    ap.add_argument("--train", action="store_true", help="Train from closed days before today")
    args = ap.parse_args()
    lm = LearningManager()
    pprint(lm.stats(args.day))
    if args.train:
        pprint(lm.train_previous_days())
