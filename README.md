# YC Startup Lead Generator & Validator

This project scrapes, analyzes, and prioritizes Y Combinator (YC) startup data to generate high-fit leads for SEO and organic growth services, with a focus on dev tools and vertical AI companies.

## What It Does
- **Scrapes and compiles** YC company data (company details, founders, tags, location, etc.)
- **Filters and scores** startups for SEO outreach using `practical_lead_finder.py` (criteria: team size, status, tags, batch year, etc.)
- **Validates leads** with `lead_validator.py` by checking company websites for tech stack (Webflow, Framer, React, etc.) and blog presence
- **Exports** prioritized, validated lead lists for practical outreach

## Usage
1. Run `practical_lead_finder.py` to generate the top 50 YC startup leads for SEO services
2. Run `lead_validator.py` to validate all 50 leads and export a final, scored list

## Requirements
- Python 3.11+
- [Scrapy](https://scrapy.org), [Selenium](https://www.selenium.dev/documentation/), [tqdm](https://tqdm.github.io), [Pandas](https://pandas.pydata.org)
- Firefox and [geckodriver](https://github.com/mozilla/geckodriver/releases) for scraping

## Data
The project uses up-to-date YC datasets (CSV) with company attributes, and outputs filtered/validated lead CSVs for outreach.

---

Distributed under the MIT license. See [LICENSE](./LICENSE) for more information.
