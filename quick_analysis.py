#!/usr/bin/env python3
"""
Quick Analysis of Y Combinator Companies Dataset
Run this script to get immediate insights about the dataset.
"""

import pandas as pd
import json
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

def parse_tags(tags_str):
    """Parse tags from string representation to list."""
    if pd.isna(tags_str) or tags_str == '[]':
        return []
    try:
        tags_str = tags_str.replace("'", '"').replace('"', '"')
        return json.loads(tags_str)
    except:
        return []

def main():
    print("🚀 Y Combinator Companies - Quick Analysis")
    print("=" * 60)
    
    # Load data
    print("📊 Loading dataset...")
    df = pd.read_csv('data/2024-05-11-yc-companies.csv')
    print(f"✅ Loaded {len(df):,} companies\n")
    
    # Basic stats
    print("📈 BASIC STATISTICS")
    print("-" * 30)
    print(f"Total companies: {len(df):,}")
    print(f"Active companies: {len(df[df['status'] == 'Active']):,}")
    print(f"Public companies: {len(df[df['status'] == 'Public']):,}")
    print(f"Acquired companies: {len(df[df['status'] == 'Acquired']):,}")
    print(f"Average team size: {df['team_size'].mean():.1f}")
    print(f"Average founders: {df['num_founders'].mean():.1f}")
    
    # Status distribution
    print(f"\n🏢 COMPANY STATUS DISTRIBUTION")
    print("-" * 30)
    status_counts = df['status'].value_counts()
    for status, count in status_counts.items():
        percentage = count / len(df) * 100
        print(f"{status}: {count:,} ({percentage:.1f}%)")
    
    # Top countries
    print(f"\n🌍 TOP 10 COUNTRIES")
    print("-" * 30)
    country_counts = df['country'].value_counts().head(10)
    for i, (country, count) in enumerate(country_counts.items(), 1):
        print(f"{i:2d}. {country}: {count:,} companies")
    
    # Top US cities
    print(f"\n🏙️  TOP 10 US CITIES")
    print("-" * 30)
    us_companies = df[df['country'] == 'US']
    city_counts = us_companies['location'].value_counts().head(10)
    for i, (city, count) in enumerate(city_counts.items(), 1):
        print(f"{i:2d}. {city}: {count:,} companies")
    
    # Top batches
    print(f"\n🎓 TOP 10 YC BATCHES")
    print("-" * 30)
    batch_counts = df['batch'].value_counts().head(10)
    for i, (batch, count) in enumerate(batch_counts.items(), 1):
        print(f"{i:2d}. {batch}: {count:,} companies")
    
    # Industry tags
    print(f"\n🏷️  TOP 15 INDUSTRY TAGS")
    print("-" * 30)
    all_tags = []
    for tags in df['tags'].apply(parse_tags):
        all_tags.extend(tags)
    
    tag_counts = Counter(all_tags)
    for i, (tag, count) in enumerate(tag_counts.most_common(15), 1):
        print(f"{i:2d}. {tag}: {count:,} companies")
    
    # Team size distribution
    print(f"\n👥 TEAM SIZE STATISTICS")
    print("-" * 30)
    print(f"Mean team size: {df['team_size'].mean():.1f}")
    print(f"Median team size: {df['team_size'].median():.1f}")
    print(f"Largest team: {df['team_size'].max():.0f}")
    print(f"Smallest team: {df['team_size'].min():.0f}")
    
    # Notable companies
    print(f"\n⭐ NOTABLE COMPANIES")
    print("-" * 30)
    print("Largest teams:")
    largest_teams = df.nlargest(5, 'team_size')[['company_name', 'team_size', 'batch', 'status']]
    for _, row in largest_teams.iterrows():
        print(f"  • {row['company_name']}: {row['team_size']:.0f} employees ({row['batch']}, {row['status']})")
    
    print("\nPublic companies (sample):")
    public_companies = df[df['status'] == 'Public'][['company_name', 'batch', 'team_size']].head(5)
    for _, row in public_companies.iterrows():
        print(f"  • {row['company_name']}: {row['team_size']:.0f} employees ({row['batch']})")
    
    print(f"\n🎯 KEY INSIGHTS")
    print("-" * 30)
    print(f"• YC has invested in {len(df):,} companies total")
    print(f"• {len(df[df['status'] == 'Active'])/len(df)*100:.1f}% are still active")
    print(f"• {len(df[df['status'] == 'Public'])/len(df)*100:.1f}% have gone public")
    print(f"• {len(df[df['status'] == 'Acquired'])/len(df)*100:.1f}% have been acquired")
    print(f"• Most companies are based in {df['country'].mode().iloc[0]}")
    print(f"• Most common industry: {tag_counts.most_common(1)[0][0]}")
    print(f"• Average team size: {df['team_size'].mean():.1f} employees")
    
    print(f"\n✅ Analysis complete! Open 'yc_companies_analysis.ipynb' for detailed visualizations.")

if __name__ == "__main__":
    main() 