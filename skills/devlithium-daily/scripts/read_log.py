"""
devlithium-daily: read_log.py
Reads the last N entries from daily_log.jsonl and prints them.
Usage: python read_log.py --last 1
"""
import json, argparse, os

LOG_PATH = os.path.join(os.path.dirname(__file__), "../../../logs/daily_log.jsonl")

def read_last(n=1):
    if not os.path.exists(LOG_PATH):
        print("No log file found. Starting fresh.")
        return []
    with open(LOG_PATH) as f:
        lines = [l.strip() for l in f if l.strip()]
    entries = [json.loads(l) for l in lines[-n:]]
    for e in entries:
        print(json.dumps(e, indent=2))
    return entries

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--last", type=int, default=1)
    args = parser.parse_args()
    read_last(args.last)
