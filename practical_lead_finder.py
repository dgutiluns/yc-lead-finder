#!/usr/bin/env python3
"""
Practical YC Lead Finder for SEO Services
Simple, effective approach using existing data.
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
    print("🎯 Practical YC Lead Finder for SEO Services")
    print("=" * 60)
    
    # Load data
    #df = pd.read_csv('data/2024-05-11-yc-companies.csv')
    df = pd.read_csv('yc_companies_filtered.csv')
    # Ensure 'tags' column exists for compatibility with both old and new datasets
    if 'tags' not in df.columns:
        if 'industry_tags' in df.columns:
            df['tags'] = df['industry_tags']
            print("🛈 Using 'industry_tags' column as 'tags'.")
        else:
            raise ValueError("No 'tags' or 'industry_tags' column found in input CSV.")
        
    if 'company_name' not in df.columns:
        if 'name' in df.columns:
            df['company_name'] = df['name']
            print("🛈 Using 'name' column as 'company_name'.")
        else:
            raise ValueError("No 'company_name' or 'name' column found in input CSV.")
        
    print(f"📊 Loaded {len(df):,} companies\n")
    
    # Parse tags
    df['tags_parsed'] = df['tags'].apply(parse_tags)
    
    # Define target industries
    target_tags = [
        'developer-tools', 'dev-tools', 'developer-tool', 'api', 'sdk',
        'artificial-intelligence', 'ai', 'machine-learning', 'ml',
        'generative-ai', 'llm', 'nlp', 'computer-vision',
        'saas', 'b2b', 'enterprise', 'productivity'
    ]
    
    print("🔍 STEP 1: Basic Filtering")
    print("-" * 40)
    
    # Basic filters
    filtered_df = df[
        (df['team_size'] > 5) &  # More than 5 employees
        (df['status'] == 'Active') &  # Active companies
        (df['website'].notna()) &  # Has website
        (df['website'] != '')  # Website not empty
    ].copy()
    
    print(f"Companies with >5 employees: {len(filtered_df)}")
    
    # Score companies based on target tags
    def calculate_fit_score(tags):
        if not tags or not isinstance(tags, list):
            return 0
        score = 0
        for tag in tags:
            if any(target in tag.lower() for target in target_tags):
                score += 1
        return score
    
    filtered_df['fit_score'] = filtered_df['tags_parsed'].apply(calculate_fit_score)
    
    # Keep companies with at least some relevance
    high_fit_df = filtered_df[filtered_df['fit_score'] > 0].copy()
    high_fit_df = high_fit_df.sort_values(['fit_score', 'team_size'], ascending=[False, False])
    
    print(f"High-fit companies (dev tools/AI): {len(high_fit_df)}")
    
    print("\n🔍 STEP 2: Recent Companies (Batches 2021+)")
    print("-" * 40)
    
    # Extract batch year and filter for 2021+ batches
    def extract_batch_year(batch_str):
        """Extract year from batch string (e.g., 'W21' -> 21, 'S22' -> 22)"""
        if pd.isna(batch_str) or batch_str == '':
            return 0
        try:
            # Extract the 2-digit year from batch string
            year_match = batch_str[-2:]  # Get last 2 characters
            return int(year_match)
        except:
            return 0
    
    high_fit_df['batch_year'] = high_fit_df['batch'].apply(extract_batch_year)
    recent_companies = high_fit_df[high_fit_df['batch_year'] >= 21].copy()
    
    print(f"Companies from 2021+ batches: {len(recent_companies)}")
    print(f"Batch range: {recent_companies['batch_year'].min()}-{recent_companies['batch_year'].max()}")
    
    print("\n🔍 STEP 3: Top Lead Candidates")
    print("-" * 40)
    
    # Show top candidates
    top_candidates = recent_companies.head(20)
    
    print("🎯 TOP 20 LEAD CANDIDATES:")
    print("=" * 60)
    
    for idx, company in top_candidates.iterrows():
        print(f"\n{idx+1:2d}. {company['company_name']}")
        print(f"    Website: {company['website']}")
        print(f"    Batch: {company['batch']} | Team: {company['team_size']} | Location: {company['location']}")
        print(f"    Fit Score: {company['fit_score']} | Tags: {', '.join(company['tags_parsed'][:3])}")
        print(f"    Description: {company['short_description'][:100]}...")
    
    print("\n🔍 STEP 4: Industry Analysis")
    print("-" * 40)
    
    # Analyze tags
    all_tags = []
    for tags in high_fit_df['tags_parsed']:
        all_tags.extend(tags)
    
    tag_counts = Counter(all_tags)
    
    print("Top Industry Tags in High-Fit Companies:")
    for i, (tag, count) in enumerate(tag_counts.most_common(15), 1):
        print(f"{i:2d}. {tag}: {count} companies")
    
    print("\n🔍 STEP 5: Geographic Distribution")
    print("-" * 40)
    
    location_counts = high_fit_df['location'].value_counts().head(10)
    print("Top Locations for High-Fit Companies:")
    for i, (location, count) in enumerate(location_counts.items(), 1):
        print(f"{i:2d}. {location}: {count} companies")
    
    print("\n🔍 STEP 6: Team Size Analysis")
    print("-" * 40)
    
    team_sizes = high_fit_df['team_size']
    print(f"Average team size: {team_sizes.mean():.1f}")
    print(f"Median team size: {team_sizes.median():.1f}")
    print(f"Range: {team_sizes.min():.0f} - {team_sizes.max():.0f}")
    
    # Companies with 10-100 employees (sweet spot)
    sweet_spot = high_fit_df[(high_fit_df['team_size'] >= 10) & (high_fit_df['team_size'] <= 100)]
    print(f"Sweet spot (10-100 employees): {len(sweet_spot)} companies")
    
    print("\n🎯 STEP 7: Actionable Lead List")
    print("-" * 40)
    
    # Apply batch filtering to the sweet spot companies
    sweet_spot['batch_year'] = sweet_spot['batch'].apply(extract_batch_year)
    recent_sweet_spot = sweet_spot[sweet_spot['batch_year'] >= 21].copy()
    
    print(f"Recent companies in sweet spot (10-100 employees, 2021+ batches): {len(recent_sweet_spot)}")
    
    # Create final lead list
    final_leads = recent_sweet_spot.head(50)[[
        'company_name', 'website', 'batch', 'team_size', 'location', 
        'fit_score', 'tags_parsed', 'short_description'
    ]].copy()
    
    print("TOP 50 ACTIONABLE LEADS:")
    print("=" * 60)
    
    for idx, lead in final_leads.iterrows():
        print(f"\n{idx+1:2d}. {lead['company_name']}")
        print(f"    🌐 {lead['website']}")
        print(f"    👥 {lead['team_size']:.0f} employees | 📍 {lead['location']}")
        print(f"    🎯 Fit Score: {lead['fit_score']} | 🏷️  {', '.join(lead['tags_parsed'][:3])}")
        print(f"    📝 {lead['short_description'][:80]}...")
    
    # Export to CSV
    final_leads.to_csv('top_50_yc_seo_leads_2025.csv', index=False)
    print(f"\n✅ Exported top 50 leads to 'top_50_yc_seo_leads_2025.csv'")
    
    print("\n🎯 NEXT STEPS:")
    print("-" * 40)
    print("1. Manually check each website for:")
    print("   • Webflow/Framer usage (inspect page source)")
    print("   • Blog presence (/blog, /articles, etc.)")
    print("   • Customer logos and testimonials")
    print("   • Content marketing activity")
    
    print("\n2. Research funding announcements:")
    print("   • Check Crunchbase for recent rounds")
    print("   • Look for press releases")
    print("   • Monitor LinkedIn for funding posts")
    
    print("\n3. Validate SEO opportunity:")
    print("   • Check current organic traffic (SimilarWeb)")
    print("   • Analyze competitor SEO activity")
    print("   • Review current content strategy")
    
    print(f"\n🎉 Analysis complete! Found {len(final_leads)} high-potential leads.")

if __name__ == "__main__":
    main() 