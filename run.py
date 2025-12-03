import sys

from src.orchestrator.main import run_pipeline


def main() -> None:
    if len(sys.argv) < 2:
        user_query = "Analyze ROAS drop"
    else:
        user_query = sys.argv[1]
    run_pipeline(user_query)


if __name__ == "__main__":
    main()
