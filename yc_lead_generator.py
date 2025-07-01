#!/usr/bin/env python3
"""
YC Lead Generator for SEO Services
Finds high-fit YC companies for SEO/organic growth services.
"""

import pandas as pd
import json
import requests
from urllib.parse import urlparse
import time
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

class YCLeadGenerator:
    def __init__(self, data_file='data/2024-05-11-yc-companies.csv'):
        self.df = pd.read_csv(data_file)
        self.leads = []
        
    def parse_tags(self, tags_str):
        """Parse tags from string representation to list."""
        if pd.isna(tags_str) or tags_str == '[]':
            return []
        try:
            tags_str = tags_str.replace("'", '"').replace('"', '"')
            return json.loads(tags_str)
        except:
            return []
    
    def filter_high_fit_companies(self):
        """Filter companies based on your criteria."""
        print("🔍 Filtering high-fit companies...")
        
        # Parse tags
        self.df['tags_parsed'] = self.df['tags'].apply(self.parse_tags)
        
        # Define target industries
        target_tags = [
            'developer-tools', 'dev-tools', 'developer-tool', 'api', 'sdk',
            'artificial-intelligence', 'ai', 'machine-learning', 'ml',
            'generative-ai', 'llm', 'nlp', 'computer-vision',
            'saas', 'b2b', 'enterprise', 'productivity'
        ]
        
        # Filter criteria
        filtered_df = self.df[
            # Team size > 5
            (self.df['team_size'] > 5) &
            # Founded after 2021 (approximate from batch)
            (self.df['batch'].str.extract(r'(\d{2})').astype(float) >= 21) &
            # Active companies
            (self.df['status'] == 'Active') &
            # Has website
            (self.df['website'].notna()) &
            (self.df['website'] != '')
        ].copy()
        
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
        filtered_df = filtered_df[filtered_df['fit_score'] > 0].copy()
        
        # Sort by fit score and team size
        filtered_df = filtered_df.sort_values(['fit_score', 'team_size'], ascending=[False, False])
        
        print(f"✅ Found {len(filtered_df)} high-fit companies")
        return filtered_df
    
    def check_tech_stack(self, website):
        """Check if website uses Webflow or Framer."""
        try:
            response = requests.get(website, timeout=10)
            html = response.text.lower()
            
            tech_stack = []
            if 'data-wf-domain' in html or 'webflow' in html:
                tech_stack.append('Webflow')
            if 'data-framer-hydrate-v2' in html or 'framer' in html:
                tech_stack.append('Framer')
            if 'shopify' in html:
                tech_stack.append('Shopify')
            if 'wordpress' in html:
                tech_stack.append('WordPress')
            if 'next.js' in html or 'nextjs' in html:
                tech_stack.append('Next.js')
            if 'react' in html:
                tech_stack.append('React')
            
            return tech_stack
        except:
            return []
    
    def check_blog_presence(self, website):
        """Check if company has a blog."""
        try:
            # Try common blog URLs
            blog_urls = [
                f"{website}/blog",
                f"{website}/articles",
                f"{website}/news",
                f"{website}/insights",
                f"{website}/resources"
            ]
            
            for blog_url in blog_urls:
                response = requests.get(blog_url, timeout=5)
                if response.status_code == 200:
                    return blog_url
            
            # Check sitemap
            sitemap_url = f"{website}/sitemap.xml"
            response = requests.get(sitemap_url, timeout=5)
            if response.status_code == 200 and 'blog' in response.text.lower():
                return "sitemap_blog"
                
            return None
        except:
            return None
    
    def enrich_company_data(self, df, sample_size=50):
        """Enrich company data with tech stack and blog information."""
        print(f"🔧 Enriching data for {sample_size} companies...")
        
        enriched_data = []
        
        for idx, row in df.head(sample_size).iterrows():
            print(f"Processing {row['company_name']}...")
            
            website = row['website']
            if not website.startswith('http'):
                website = f"https://{website}"
            
            # Check tech stack
            tech_stack = self.check_tech_stack(website)
            
            # Check blog presence
            blog_url = self.check_blog_presence(website)
            
            enriched_row = {
                'company_name': row['company_name'],
                'website': website,
                'batch': row['batch'],
                'team_size': row['team_size'],
                'status': row['status'],
                'location': row['location'],
                'country': row['country'],
                'tags': row['tags_parsed'],
                'fit_score': row['fit_score'],
                'tech_stack': tech_stack,
                'blog_url': blog_url,
                'short_description': row['short_description']
            }
            
            enriched_data.append(enriched_row)
            time.sleep(1)  # Be respectful to servers
        
        return pd.DataFrame(enriched_data)
    
    def generate_lead_report(self, enriched_df):
        """Generate a comprehensive lead report."""
        print("\n📊 LEAD GENERATION REPORT")
        print("=" * 60)
        
        # Priority 1: Webflow/Framer companies with blogs
        priority_1 = enriched_df[
            (enriched_df['tech_stack'].apply(lambda x: 'Webflow' in x or 'Framer' in x)) &
            (enriched_df['blog_url'].notna())
        ]
        
        # Priority 2: High fit score companies with blogs
        priority_2 = enriched_df[
            (enriched_df['fit_score'] >= 2) &
            (enriched_df['blog_url'].notna())
        ]
        
        # Priority 3: All other high-fit companies
        priority_3 = enriched_df[enriched_df['fit_score'] >= 2]
        
        print(f"\n🎯 PRIORITY 1 (Webflow/Framer + Blog): {len(priority_1)} companies")
        print("-" * 50)
        for _, company in priority_1.iterrows():
            print(f"• {company['company_name']} ({company['website']})")
            print(f"  Batch: {company['batch']}, Team: {company['team_size']}, Tech: {company['tech_stack']}")
            print(f"  Blog: {company['blog_url']}")
            print()
        
        print(f"\n🔥 PRIORITY 2 (High Fit + Blog): {len(priority_2)} companies")
        print("-" * 50)
        for _, company in priority_2.head(10).iterrows():
            print(f"• {company['company_name']} ({company['website']})")
            print(f"  Fit Score: {company['fit_score']}, Team: {company['team_size']}")
            print(f"  Tags: {', '.join(company['tags'][:3])}")
            print()
        
        print(f"\n📈 ALL HIGH-FIT COMPANIES: {len(priority_3)} companies")
        print("-" * 50)
        
        # Tech stack distribution
        all_tech = []
        for tech_list in enriched_df['tech_stack']:
            all_tech.extend(tech_list)
        
        tech_counts = Counter(all_tech)
        print("Tech Stack Distribution:")
        for tech, count in tech_counts.most_common():
            print(f"  {tech}: {count} companies")
        
        # Blog presence
        blog_count = len(enriched_df[enriched_df['blog_url'].notna()])
        print(f"\nBlog Presence: {blog_count}/{len(enriched_df)} companies ({blog_count/len(enriched_df)*100:.1f}%)")
        
        return {
            'priority_1': priority_1,
            'priority_2': priority_2,
            'priority_3': priority_3,
            'enriched_data': enriched_df
        }
    
    def export_leads(self, report_data, filename='yc_seo_leads.csv'):
        """Export leads to CSV."""
        # Combine all priorities
        all_leads = pd.concat([
            report_data['priority_1'].assign(priority='Priority 1'),
            report_data['priority_2'].assign(priority='Priority 2'),
            report_data['priority_3'].assign(priority='Priority 3')
        ]).drop_duplicates(subset=['company_name'])
        
        # Clean up for export
        export_df = all_leads[[
            'company_name', 'website', 'batch', 'team_size', 'location', 
            'fit_score', 'tech_stack', 'blog_url', 'priority', 'tags'
        ]].copy()
        
        export_df.to_csv(filename, index=False)
        print(f"\n✅ Exported {len(export_df)} leads to {filename}")
        
        return export_df

def main():
    print("🚀 YC Lead Generator for SEO Services")
    print("=" * 60)
    
    # Initialize generator
    generator = YCLeadGenerator()
    
    # Filter high-fit companies
    filtered_df = generator.filter_high_fit_companies()
    
    # Enrich with tech stack and blog data
    enriched_df = generator.enrich_company_data(filtered_df, sample_size=100)
    
    # Generate report
    report = generator.generate_lead_report(enriched_df)
    
    # Export leads
    leads_df = generator.export_leads(report)
    
    print(f"\n🎉 Lead generation complete!")
    print(f"Total leads found: {len(leads_df)}")
    print(f"Priority 1: {len(report['priority_1'])}")
    print(f"Priority 2: {len(report['priority_2'])}")
    print(f"Priority 3: {len(report['priority_3'])}")

if __name__ == "__main__":
    main() 