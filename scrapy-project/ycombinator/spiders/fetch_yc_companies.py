import requests
import pandas as pd
import time

# Adjust these if you want to pull more companies
LIMIT = 100  # Number of companies per batch
MAX_COMPANIES = 2000  # Total number of companies you want to fetch

def fetch_yc_companies(limit=LIMIT, offset=0):
    """
    Fetch a single batch of YC companies from the YC API.
    """
    url = f"https://api.ycombinator.com/v0/companies?limit={limit}&offset={offset}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch offset {offset}: status code {response.status_code}")
        return []

def main():
    all_companies = []
    offset = 0

    while offset < MAX_COMPANIES:
        companies = fetch_yc_companies(limit=LIMIT, offset=offset)
        if not companies:
            break  # Stop if no more data
        all_companies.extend(companies)
        print(f"Fetched {len(companies)} companies (offset: {offset})")
        offset += LIMIT
        time.sleep(1)  # Avoid hammering the server

    # Convert to DataFrame
    df = pd.DataFrame(all_companies)

    # Save to CSV
    df.to_csv("yc_companies_full.csv", index=False)
    print(f"Saved {len(df)} companies to yc_companies_full.csv")

if __name__ == "__main__":
    main()
