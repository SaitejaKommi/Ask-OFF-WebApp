import argparse
import logging
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from pipeline.runner import run_pipeline  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the data ingestion pipeline")
    parser.add_argument("--csv", help="Path to raw CSV file")
    parser.add_argument(
        "--batch-size", type=int, default=5000, help="Batch size for processing"
    )
    args = parser.parse_args()

    output = run_pipeline(csv_path=args.csv)
    print(f"Pipeline output: {output}")
