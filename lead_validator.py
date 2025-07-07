#!/usr/bin/env python3
"""
Lead Validator for YC SEO Leads
Quick validation of tech stack and blog presence.
"""

import pandas as pd
import requests
import time
from urllib.parse import urljoin
import warnings
warnings.filterwarnings('ignore')

def check_tech_stack(website):
    """Check if website uses Webflow, Framer, or other platforms."""
    try:
        response = requests.get(website, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
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
        if 'vue' in html:
            tech_stack.append('Vue')
        if 'angular' in html:
            tech_stack.append('Angular')
        
        return tech_stack
    except Exception as e:
        return [f"Error: {str(e)[:20]}"]

def check_blog_presence(website):
    """Check if company has a blog."""
    try:
        # Common blog URL patterns
        blog_patterns = [
            '/blog', '/articles', '/news', '/insights', '/resources',
            '/content', '/stories', '/updates', '/journal'
        ]
        
        for pattern in blog_patterns:
            blog_url = urljoin(website, pattern)
            try:
                response = requests.get(blog_url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    return blog_url
            except:
                continue
        
        # Check sitemap
        try:
            sitemap_url = urljoin(website, '/sitemap.xml')
            response = requests.get(sitemap_url, timeout=5)
            if response.status_code == 200 and 'blog' in response.text.lower():
                return "sitemap_blog"
        except:
            pass
            
        return None
    except Exception as e:
        return f"Error: {str(e)[:20]}"

def extract_customers_partners(website):
    """Extract customer or partner information from company website."""
    try:
        # Common customer/partner page patterns
        customer_patterns = [
            '/customers', '/case-studies', '/partners', '/clients',
            '/success-stories', '/testimonials', '/trusted-by',
            '/who-uses', '/customers-success', '/partners-customers'
        ]
        
        customers_found = []
        
        # Check main page first
        try:
            response = requests.get(website, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            html = response.text.lower()
            
            # Look for common customer indicators in main page
            customer_indicators = [
                'trusted by', 'used by', 'powering', 'customers include',
                'partners include', 'clients include', 'success stories',
                'case studies', 'testimonials'
            ]
            
            for indicator in customer_indicators:
                if indicator in html:
                    # Extract text around these indicators
                    start_idx = html.find(indicator)
                    if start_idx != -1:
                        # Get surrounding text (500 characters)
                        surrounding_text = html[max(0, start_idx-250):start_idx+250]
                        # Look for company names (capitalized words)
                        import re
                        potential_companies = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', surrounding_text)
                        customers_found.extend(potential_companies[:5])  # Limit to 5
        except:
            pass
        
        # Check specific customer/partner pages
        for pattern in customer_patterns:
            customer_url = urljoin(website, pattern)
            try:
                response = requests.get(customer_url, timeout=8, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    html = response.text.lower()
                    
                    # Look for company names in customer pages
                    import re
                    # Common patterns for company names in customer sections
                    company_patterns = [
                        r'<h[1-6][^>]*>([^<]+)</h[1-6]>',  # Headers
                        r'<div[^>]*class="[^"]*logo[^"]*"[^>]*>([^<]+)</div>',  # Logo divs
                        r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',  # Company spans
                    ]
                    
                    for pattern in company_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        for match in matches:
                            # Clean up the match
                            clean_match = re.sub(r'[^\w\s]', '', match).strip()
                            if len(clean_match) > 2 and len(clean_match) < 50:
                                customers_found.append(clean_match)
                    
                    # Also look for alt text in images (often company logos)
                    img_pattern = r'<img[^>]*alt="([^"]*)"[^>]*>'
                    img_matches = re.findall(img_pattern, html, re.IGNORECASE)
                    for match in img_matches:
                        clean_match = re.sub(r'[^\w\s]', '', match).strip()
                        if len(clean_match) > 2 and len(clean_match) < 50:
                            customers_found.append(clean_match)
                            
            except:
                continue
        
        # Remove duplicates and common false positives
        unique_customers = []
        false_positives = ['home', 'about', 'contact', 'privacy', 'terms', 'login', 'signup', 'menu', 'search']
        
        for customer in customers_found:
            customer_clean = customer.strip()
            if (customer_clean not in unique_customers and 
                customer_clean not in false_positives and
                len(customer_clean) > 2):
                unique_customers.append(customer_clean)
        
        return unique_customers[:10] if unique_customers else []  # Limit to 10 customers
        
    except Exception as e:
        return []

def validate_leads(csv_file='top_50_yc_seo_leads.csv', sample_size=None):
    """Validate leads from CSV file."""
    print("🔍 Lead Validator for YC SEO Leads")
    print("=" * 50)
    
    # Load leads
    df = pd.read_csv(csv_file)
    print(f"📊 Loaded {len(df)} leads from {csv_file}")
    
    # Validate all companies or sample
    if sample_size is None:
        sample_df = df  # Validate all companies
        print(f"\n🔧 Validating ALL {len(sample_df)} companies...")
    else:
        sample_df = df.head(sample_size)  # Validate sample
        print(f"\n🔧 Validating {len(sample_df)} companies...")
    print("-" * 50)
    
    validated_data = []
    
    for idx, row in sample_df.iterrows():
        print(f"\n{idx+1:2d}. {row['company_name']}")
        print(f"    Website: {row['website']}")
        
        # Check tech stack
        tech_stack = check_tech_stack(row['website'])
        print(f"    Tech Stack: {', '.join(tech_stack) if tech_stack else 'Unknown'}")
        
        # Check blog
        blog_url = check_blog_presence(row['website'])
        print(f"    Blog: {blog_url if blog_url else 'Not found'}")
        
        # Extract customers/partners
        customers_partners = extract_customers_partners(row['website'])
        print(f"    Customers/Partners: {', '.join(customers_partners) if customers_partners else 'None found'}")
        
        # Store results
        validated_data.append({
            'company_name': row['company_name'],
            'website': row['website'],
            'batch': row['batch'],
            'team_size': row['team_size'],
            'fit_score': row['fit_score'],
            'tech_stack': tech_stack,
            'blog_url': blog_url,
            'customers_or_partners': customers_partners,
            'location': row['location']
        })
        
        time.sleep(1)  # Be respectful
    
    # Create validation report
    validated_df = pd.DataFrame(validated_data)
    
    print(f"\n📊 VALIDATION REPORT")
    print("=" * 50)
    
    # Tech stack analysis
    all_tech = []
    for tech_list in validated_df['tech_stack']:
        if isinstance(tech_list, list):
            all_tech.extend(tech_list)
    
    tech_counts = {}
    for tech in all_tech:
        if tech not in tech_counts:
            tech_counts[tech] = 0
        tech_counts[tech] += 1
    
    print("Tech Stack Distribution:")
    for tech, count in sorted(tech_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tech}: {count} companies")
    
    # Blog presence
    blog_count = len(validated_df[validated_df['blog_url'].notna()])
    print(f"\nBlog Presence: {blog_count}/{len(validated_df)} companies ({blog_count/len(validated_df)*100:.1f}%)")
    
    # Priority scoring
    def calculate_priority_score(row):
        score = 0
        # Tech stack bonus
        if isinstance(row['tech_stack'], list):
            if 'Webflow' in row['tech_stack'] or 'Framer' in row['tech_stack']:
                score += 3
            if 'Next.js' in row['tech_stack'] or 'React' in row['tech_stack']:
                score += 2
        
        # Blog bonus
        if row['blog_url'] and row['blog_url'] != 'None':
            score += 2
        
        # Team size bonus (10-50 employees is ideal)
        if 10 <= row['team_size'] <= 50:
            score += 1
        
        return score
    
    validated_df['priority_score'] = validated_df.apply(calculate_priority_score, axis=1)
    validated_df = validated_df.sort_values('priority_score', ascending=False)
    
    print(f"\n🎯 TOP PRIORITY LEADS:")
    print("=" * 50)
    
    for idx, row in validated_df.head(5).iterrows():
        print(f"\n{idx+1}. {row['company_name']}")
        print(f"   Website: {row['website']}")
        print(f"   Priority Score: {row['priority_score']}")
        print(f"   Tech: {', '.join(row['tech_stack']) if isinstance(row['tech_stack'], list) else row['tech_stack']}")
        print(f"   Blog: {row['blog_url']}")
        print(f"   Team: {row['team_size']} employees")
    
    # Export validated leads
    validated_df.to_csv('validated_yc_leads.csv', index=False)
    print(f"\n✅ Exported validated leads to 'validated_yc_leads.csv'")
    
    return validated_df

if __name__ == "__main__":
    # Validate all leads
    validated_leads = validate_leads(sample_size=None) 