#!/usr/bin/env python3
"""
YC Directory Scraper
Minimal Playwright-based scraper for YC company directory.
"""

import asyncio
import pandas as pd
import time
import random
from playwright.async_api import async_playwright
import json
import re
from urllib.parse import urljoin
import ast

class YCDirectoryScraper:
    def __init__(self):
        self.companies = []
        # Use the new US-only filtered URL
        self.filtered_url = "https://www.ycombinator.com/companies?batch=Winter%202025&batch=Spring%202025&batch=Summer%202025&batch=Fall%202024&batch=Summer%202024&regions=United%20States%20of%20America"
        
    async def init_browser(self):
        """Initialize browser with proper settings."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Set to True for production
            slow_mo=1000  # Add delay to avoid detection
        )
        self.page = await self.browser.new_page()
        
        # Set user agent
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    async def scrape_filtered_companies(self):
        """Scrape companies from the filtered URL."""
        print("🔍 Scraping filtered companies from YC directory...")
        
        try:
            # Navigate to filtered YC companies page
            await self.page.goto(self.filtered_url)
            await self.page.wait_for_load_state('networkidle')
            
            print("📄 Page loaded, extracting companies...")
            
            # Extract all companies from the filtered page
            await self.extract_all_companies()
            
        except Exception as e:
            print(f"❌ Error scraping filtered companies: {e}")
            
    async def extract_all_companies(self, max_pages=35):
        """Collect all unique company slugs/names during scrolling, then scrape each detail page only once. Limit to first page for fast testing."""
        print("🔍 Extracting all companies from filtered page...")
        page_count = 0
        unique_companies = {}  # slug -> name
        while True:
            page_count += 1
            print(f"\n📄 Processing page {page_count}...")
            await self.page.wait_for_timeout(2000)
            # Collect all company cards currently in the DOM
            company_cards = await self.page.query_selector_all('div._section_i9oky_163._results_i9oky_343 > a')
            for card in company_cards:
                # Extract slug and name for deduplication
                href = await card.get_attribute('href')
                slug = href.split('/companies/')[-1].strip('/') if href and href.startswith('/companies/') else None
                name_el = await card.query_selector('span._coName_i9oky_470')
                name = await name_el.inner_text() if name_el else ""
                if slug and slug not in unique_companies:
                    unique_companies[slug] = name
            print(f"🔎 Unique companies collected so far: {len(unique_companies)}")
            if page_count >= max_pages:
                print(f"🛑 Reached max_pages ({max_pages}), stopping for test.")
                break
            more_companies = await self.load_more_companies()
            if not more_companies:
                print("🏁 No more companies to load")
                break
            if page_count > 50:
                print("⚠️  Reached maximum page limit (50), stopping...")
                break
        print(f"🎉 Total unique companies collected: {len(unique_companies)}")
        # Now, visit each unique company detail page only once
        for slug, name in unique_companies.items():
            try:
                company_data = await self.extract_company_data_from_slug(slug, name)
                if company_data and company_data.get('name'):
                    self.companies.append(company_data)
                    print(f"📝 Extracted: {company_data.get('name', 'Unknown')}")
            except Exception as e:
                print(f"⚠️  Error extracting company: {e}")
                continue

    async def extract_company_data_from_slug(self, slug, name):
        """Given a slug and name, visit the detail page and extract all fields."""
        detail_data = await self.scrape_company_detail_page(slug)
        # Ensure short_description is always present
        if 'short_description' not in detail_data:
            detail_data['short_description'] = ''
        company_data = {
            'name': name,
            'slug': slug,
            **detail_data,
            'scraped_at': pd.Timestamp.now().isoformat()
        }
        # Debug: Print what we extracted (only for first few companies)
        if len(self.companies) < 3:
            print(f"🔍 Debug - Extracted data: {company_data}")
        return company_data

    async def scrape_company_detail_page(self, slug):
        """Visit the company detail page and extract detailed fields using robust selectors, including industry/type tags and short_description."""
        detail_url = f"https://www.ycombinator.com/companies/{slug}"
        detail_data = {}
        try:
            detail_page = await self.browser.new_page()
            await detail_page.goto(detail_url, timeout=60000)
            await detail_page.wait_for_load_state('networkidle', timeout=60000)
            await detail_page.wait_for_timeout(2000)
            # Extract the main detail block
            detail_block = await detail_page.query_selector('div.space-y-2.pt-4')
            if detail_block:
                rows = await detail_block.query_selector_all('div.flex.flex-row.justify-between')
                for row in rows:
                    label_span = await row.query_selector('span')
                    value_span = await row.query_selector_all('span')
                    if label_span and value_span:
                        label = (await label_span.inner_text()).strip(':').strip()
                        if len(value_span) > 1:
                            value = (await value_span[1].inner_text()).strip()
                        else:
                            value = (await row.inner_text()).replace(label, '').strip(':').strip()
                        field_map = {
                            'Founded': 'year_founded',
                            'Batch': 'batch',
                            'Team Size': 'team_size',
                            'Status': 'status',
                            'Location': 'location',
                            'Primary Partner': 'primary_partner',
                        }
                        if label in field_map:
                            detail_data[field_map[label]] = value
                        if label == 'Primary Partner':
                            partner_a = await row.query_selector('a')
                            if partner_a:
                                detail_data['primary_partner'] = (await partner_a.inner_text()).strip()
            # Extract website link using robust selector
            website_link = ''
            website_a = await detail_page.query_selector('a[aria-label="Company website"]')
            if website_a:
                website_link = await website_a.get_attribute('href')
            detail_data['website'] = website_link
            # Extract industry/type tags (excluding batch and status tags)
            industry_tags = []
            tag_parent = await detail_page.query_selector('div.align-center.flex.flex-row.flex-wrap.gap-x-2.gap-y-2')
            if tag_parent:
                tag_links = await tag_parent.query_selector_all('a')
                for tag_link in tag_links:
                    href = await tag_link.get_attribute('href')
                    if href and href.startswith('/companies?batch='):
                        continue
                    tag_div = await tag_link.query_selector('div')
                    tag_text = await tag_div.inner_text() if tag_div else ""
                    if 'rounded-full' in (await tag_div.get_attribute('class') if tag_div else "") or 'Active' in tag_text:
                        continue
                    if tag_text:
                        industry_tags.append(tag_text.strip())
            detail_data['industry_tags'] = industry_tags
            # Extract short_description
            short_desc_el = await detail_page.query_selector('div.prose.max-w-full.whitespace-pre-line')
            short_description = await short_desc_el.inner_text() if short_desc_el else ""
            detail_data['short_description'] = short_description.strip()
            await detail_page.close()
        except Exception as e:
            print(f"⚠️  Error scraping detail page for {slug}: {e}")
            try:
                await detail_page.close()
            except:
                pass
        return detail_data
        
    async def extract_text(self, element, selectors):
        """Extract text from element using multiple selectors."""
        for selector in selectors:
            try:
                text_el = await element.query_selector(selector)
                if text_el:
                    text = await text_el.inner_text()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return ""
        
    async def extract_href(self, element, selectors):
        """Extract href from element using multiple selectors."""
        for selector in selectors:
            try:
                link_el = await element.query_selector(selector)
                if link_el:
                    href = await link_el.get_attribute('href')
                    if href and href.startswith('http'):
                        return href
            except:
                continue
        return ""
        
    async def extract_tags(self, element, selectors):
        """Extract tags from element."""
        tags = []
        for selector in selectors:
            try:
                tag_elements = await element.query_selector_all(selector)
                for tag_el in tag_elements:
                    tag_text = await tag_el.inner_text()
                    if tag_text and len(tag_text.strip()) < 50:  # Reasonable tag length
                        tags.append(tag_text.strip())
            except:
                continue
        return list(set(tags))  # Remove duplicates
        
    async def load_more_companies(self):
        """Load more companies if available."""
        try:
            # Get current number of company elements
            current_companies = await self.page.query_selector_all('[class*="company"]')
            current_count = len(current_companies)
            
            # Look for "Load More" button or infinite scroll
            load_more_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                'button:has-text("Load More Companies")',
                '[class*="load-more"]',
                '[class*="pagination"]',
                'button[aria-label*="load"]',
                'button[aria-label*="more"]'
            ]
            
            for selector in load_more_selectors:
                try:
                    load_more = await self.page.query_selector(selector)
                    if load_more:
                        # Check if button is visible and clickable
                        is_visible = await load_more.is_visible()
                        if is_visible:
                            print("🔄 Found Load More button, clicking...")
                            await load_more.click()
                            await self.page.wait_for_timeout(3000)  # Wait for new content
                            
                            # Check if new companies were loaded
                            new_companies = await self.page.query_selector_all('[class*="company"]')
                            if len(new_companies) > current_count:
                                print(f"✅ Loaded {len(new_companies) - current_count} more companies")
                                return True
                            else:
                                print("⚠️  No new companies loaded after clicking Load More")
                                return False
                except Exception as e:
                    print(f"⚠️  Error with load more selector {selector}: {e}")
                    continue
            
            # Try scrolling to bottom to trigger infinite scroll
            try:
                print("📜 Trying to scroll to bottom...")
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(2000)
                
                # Check if new content loaded
                new_companies = await self.page.query_selector_all('[class*="company"]')
                if len(new_companies) > current_count:
                    print(f"✅ Loaded {len(new_companies) - current_count} more companies via scroll")
                    return True
                else:
                    print("🏁 No more companies to load")
                    return False
                    
            except Exception as e:
                print(f"⚠️  Error with scroll: {e}")
            
            return False
                    
        except Exception as e:
            print(f"⚠️  Error handling pagination: {e}")
            return False
            
    async def save_to_csv(self, filename="yc_companies_filtered.csv"):
        """Save scraped data to CSV with all required fields and compatible column names for downstream scripts."""
        print("[DEBUG] Entering save_to_csv")
        if self.companies:
            print("[DEBUG] Creating DataFrame from self.companies")
            df = pd.DataFrame(self.companies)
            print("[DEBUG] DataFrame created. Columns:", df.columns.tolist())
            # Rename columns for compatibility
            df = df.rename(columns={'name': 'company_name', 'industry_tags': 'tags'})
            print("[DEBUG] Columns after renaming:", df.columns.tolist())
            # Ensure tags is a stringified list for compatibility
            if 'tags' in df.columns:
                def safe_stringify_tags(x):
                    if x is None or (isinstance(x, float) and pd.isna(x)):
                        return '[]'
                    elif isinstance(x, list):
                        return str(x)
                    else:
                        return str(x)
                
                df['tags'] = df['tags'].apply(safe_stringify_tags)
                #df['tags'] = df['tags'].apply(lambda x: str(x) if not pd.isna(x) else '[]')
            print("[DEBUG] Columns before ensuring all required columns:", df.columns.tolist())
            # Ensure all required columns are present
            for col in ['company_name','slug','year_founded','batch','team_size','status','location','primary_partner','website','tags','short_description','scraped_at']:
                if col not in df.columns:
                    df[col] = ''
            print("[DEBUG] Columns after ensuring all required columns:", df.columns.tolist())
            print("[DEBUG] Attempting to reorder columns")
            df = df[['company_name','slug','year_founded','batch','team_size','status','location','primary_partner','website','tags','short_description','scraped_at']]
            print("[DEBUG] Columns after reordering:", df.columns.tolist())
            print("[DEBUG] Attempting to write to CSV")
            df.to_csv(filename, index=False)
            print(f"✅ Saved {len(self.companies)} companies to {filename}")
            print(f"\n📊 Data Summary:")
            print(f"   Total companies: {len(self.companies)}")
            # Commented out problematic print statements to avoid ambiguous truth value errors
            # website_count = len(df[df['website'].notna() & (df['website'] != '')])
            # print(f"   Companies with websites: {website_count}")
            # location_count = len(df[df['location'].notna() & (df['location'] != '')])
            # print(f"   Companies with locations: {location_count}")
            # desc_count = len(df[df['short_description'].notna() & (df['short_description'] != '')])
            # print(f"   Companies with short descriptions: {desc_count}")
            # def is_nonempty_taglist(x):
            #    try:
            #        if not isinstance(x, str) or x == '[]':
            #            return False
            #        val = ast.literal_eval(x)
            #        return isinstance(val, list) and len(val) > 0
            #    except Exception:
            #        return False
            # tags_count = df['tags'].apply(is_nonempty_taglist).sum()
            #print(f"   Companies with tags: {tags_count}")
            return df
        else:
            print("❌ No companies to save")
            return None
            
    async def close(self):
        """Close browser and cleanup."""
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

async def main():
    """Main function to run the scraper."""
    scraper = YCDirectoryScraper()
    
    try:
        await scraper.init_browser()
        await scraper.scrape_filtered_companies()
        await scraper.save_to_csv()
        
    except Exception as e:
        print(f"❌ Error in main: {e}")
        
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main()) 