import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.dependencies import get_recommender
from app.services.sync_dataset import sync_dataset_to_supabase


def main() -> None:
    recommender = get_recommender()
    result = sync_dataset_to_supabase(recommender, include_ratings=False)
    print(f"Synced {result['movies']} movies and {result['ratings']} ratings.")


if __name__ == "__main__":
    main()
