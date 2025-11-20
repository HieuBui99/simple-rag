from prefect import flow, task
from prefect.artifacts import create_markdown_artifact
from datetime import datetime
import requests

# --- Configuration ---
API_URL = 'https://graphql.anilist.co'
TOP_N = 50

@task(name="Determine Current Season")
def get_current_season_info():
    """
    Calculates the current Anime season based on the current month.
    Returns a tuple: (YEAR, SEASON_STRING)
    """
    now = datetime.now()
    month = now.month
    year = now.year

    if 1 <= month <= 3:
        return year, "WINTER"
    elif 4 <= month <= 6:
        return year, "SPRING"
    elif 7 <= month <= 9:
        return year, "SUMMER"
    else:
        return year, "FALL"

@task(
    name="Fetch Anime Data",
    retries=3,
    retry_delay_seconds=[5, 10, 20],
    log_prints=True
)
def fetch_anime_data(year: int, season: str):
    """
    Queries Anilist for the top 50 anime of the specified season.
    """
    print(f"Requesting data for {season} {year}...")
    
    query = '''
    query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int) {
        Page (page: $page, perPage: $perPage) {
            media (season: $season, seasonYear: $seasonYear, type: ANIME, sort: [POPULARITY_DESC]) {
                id
                title {
                    english
                    romaji
                }
                genres
                format
                episodes
                averageScore
            }
        }
    }
    '''
    
    variables = {
        'season': season,
        'seasonYear': year,
        'page': 1,
        'perPage': TOP_N
    }

    try:
        response = requests.post(API_URL, json={'query': query, 'variables': variables}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['data']['Page']['media']
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        raise # Trigger Prefect retry

@task(name="Generate Report")
def create_report(anime_list, year, season):
    """
    Formats the data into a Markdown table and saves it as a Prefect Artifact.
    """
    markdown_rows = []
    markdown_rows.append(f"# Top Anime for {season} {year}")
    markdown_rows.append(f"**Total Fetched:** {len(anime_list)}")
    markdown_rows.append("")
    markdown_rows.append("| Rank | Title | Score | Format | Episodes |")
    markdown_rows.append("|:---|:---|:---|:---|:---|")

    for idx, anime in enumerate(anime_list, 1):
        title = anime['title']['english'] or anime['title']['romaji'] or "N/A"
        score = anime.get('averageScore', 'N/A')
        fmt = anime.get('format', 'N/A')
        eps = anime.get('episodes', '?')
        
        # Escape pipes in titles to prevent table breaking
        title = title.replace("|", "-")
        
        markdown_rows.append(f"| {idx} | {title} | {score} | {fmt} | {eps} |")

    report_content = "\n".join(markdown_rows)
    
    # # Create artifact in Prefect UI
    # create_markdown_artifact(
    #     key="seasonal-anime-report",
    #     markdown=report_content,
    #     description=f"Top {len(anime_list)} Anime for {season} {year}"
    # )
    
    return report_content

@flow(name="Seasonal Anime Fetcher", log_prints=True)
def anime_season_flow():
    # 1. Determine Context
    year, season = get_current_season_info()
    
    # 2. Fetch Data
    anime_data = fetch_anime_data(year, season)
    
    # 3. Report
    report = create_report(anime_data, year, season)
    print(report)
    print(f"Flow complete. Report generated for {season} {year}.")

if __name__ == "__main__":
    # Serves the flow with a Cron schedule
    # 0 0 1 1,4,7,10 * -> At 00:00 on day-of-month 1 in Jan, Apr, Jul, and Oct.
    anime_season_flow.deploy(
        name="quarterly-anime-deployment",
        cron="0 0 1 1,4,7,10 *",
        tags=["anime", "etl", "quarterly"],
        work_pool_name="docker-work-pool",
        push=False,
        image="test-image:tag"
    )
    # anime_season_flow()