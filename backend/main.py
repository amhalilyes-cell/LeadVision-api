from dotenv import load_dotenv
load_dotenv()

from backend.youtube import search_youtube
from backend.market import analyze_market

def main():
    print("\n🚀 Starting YouTube Market Scanner...\n")

    videos = search_youtube("alex hormozi")

    print(f"\nFound {len(videos)} videos\n")

    results = analyze_market(videos)

    print("\n=== TOP OPPORTUNITIES ===\n")
    for r in results[:10]:
        print(
            f"{int(r['score'])} | "
            f"{int(r['views_per_day'])} v/d | "
            f"{round(r['like_rate']*100,2)}% | "
            f"{r['title']}"
        )

if __name__ == "__main__":
    main()