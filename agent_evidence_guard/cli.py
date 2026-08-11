import json
import sys
from pathlib import Path
from .core import evaluate

def main() -> None:
    if len(sys.argv) != 2:
        print("usage: agent-evidence-guard <input.json>", file=sys.stderr)
        raise SystemExit(64)
    path = Path(sys.argv[1])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision": "ERROR", "reason": str(exc)}))
        raise SystemExit(64)
    verdict = evaluate(payload)
    print(json.dumps(verdict.to_dict(), indent=2, sort_keys=True))
    raise SystemExit(0 if verdict.decision == "ALLOW" else 2)

if __name__ == "__main__":
    main()
