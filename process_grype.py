import sys
import json
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

def load_grype_json():
    """
    Loads a Grype JSON report.
    - Works if a file path is provided:  python process_grype.py grype-report.json
    - Works if data is piped in:         Get-Content grype-report.json | python process_grype.py
    - Defaults to 'grype-report.json' if nothing is passed.
    Handles UTF-8 with or without BOM automatically.
    """
    # Case 1: File path passed as argument
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            raise FileNotFoundError(f"❌ Input file not found: {path}")
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)

    # Case 2: Data piped via stdin
    if not sys.stdin.isatty():
        text = sys.stdin.read()
        # Remove BOM if present
        text = text.lstrip("\ufeff")
        return json.loads(text)

    # Case 3: Default file fallback
    default = Path("grype-report.json")
    if default.exists():
        with default.open("r", encoding="utf-8-sig") as f:
            return json.load(f)

    raise SystemExit(
        "⚠️  No input JSON found.\n"
        "Usage examples:\n"
        "  python process_grype.py grype-report.json\n"
        "  Get-Content grype-report.json | python process_grype.py"
    )

def main():
    try:
        data = load_grype_json()

        vulnerabilities_by_severity = defaultdict(list)
        severity_counts = defaultdict(int)

        matches = data.get("matches", [])
        if not matches:
            print("No 'matches' found in JSON — is this a valid Grype report?")
            return

        for match in matches:
            severity = match.get("vulnerability", {}).get("severity", "Unknown")
            pkg = match.get("artifact", {}).get("name", "Unknown Package")
            vulnerabilities_by_severity[severity].append(pkg)
            severity_counts[severity] += 1

        # Print categorized summary
        print("\n--- Categorized Vulnerability Report ---")
        for level in ["Critical", "High", "Medium", "Low", "Unknown"]:
            pkgs = sorted(set(vulnerabilities_by_severity.get(level, [])))
            if pkgs:
                print(f"\n[{level.upper()}] VULNERABILITIES:")
                for p in pkgs:
                    print(f"  - {p}")
        print("\n" + "=" * 45 + "\n")

        # Bar chart visualization
        order = ["Low", "Medium", "High", "Critical"]
        severities = [s for s in order if s in severity_counts]
        counts = [severity_counts[s] for s in severities]

        fig, ax = plt.subplots(figsize=(10, 7))
        bars = ax.bar(severities, counts,
                      color=["#32CD32", "#FFD700", "#FF4500", "#DC143C"])
        ax.set_xlabel("Severity", fontsize=12)
        ax.set_ylabel("Number of Vulnerabilities", fontsize=12)
        ax.set_title("Grype Vulnerability Report by Severity", fontsize=14)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        plt.savefig("vulnerability_bar_chart.png")
        print("✅ Bar chart saved as vulnerability_bar_chart.png")

    except json.JSONDecodeError as e:
        print(f"❌ Error: Could not decode the JSON file. Details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
