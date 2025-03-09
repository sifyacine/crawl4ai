import json
import os
from typing import List, Set, Tuple

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMConfig,
    LLMExtractionStrategy,
)

from models.venue import Venue
from utils.data_utils import is_complete_venue, is_duplicate_venue


def get_browser_config() -> BrowserConfig:
    """
    Returns the browser configuration for the crawler.

    Returns:
        BrowserConfig: The configuration settings for the browser.
    """
    return BrowserConfig(
        browser_type="chromium",  # Type of browser to simulate
        headless=False,           # Run with GUI for debugging
        verbose=True,             # Enable verbose logging
    )


def get_llm_strategy() -> LLMExtractionStrategy:
    """
    Returns the configuration for the language model extraction strategy.

    Returns:
        LLMExtractionStrategy: The settings for how to extract data using LLM.
    """
    return LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="groq/deepseek-r1-distill-llama-70b",  # LLM provider
            api_token=os.getenv("GROQ_API_KEY"),            # API token from environment
        ),
        schema=Venue.model_json_schema(),                 # JSON schema of the Venue model
        extraction_type="schema",                         # Extraction type
        instruction=(
            "Extract all venue objects with 'name', 'location', 'price', 'capacity', "
            "'rating', 'reviews', and a 1 sentence description of the venue from the "
            "following content."
        ),
        input_format="markdown",                          # Input content format
        verbose=True,                                     # Enable verbose logging
    )


async def check_no_results(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
) -> bool:
    """
    Checks if the "No Results Found" message is present on the page.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        url (str): The URL to check.
        session_id (str): The session identifier.

    Returns:
        bool: True if "No Results Found" is found, False otherwise.
    """
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
        ),
    )

    if result.success:
        if "No Results Found" in result.cleaned_html:
            return True
    else:
        print(f"Error fetching page for 'No Results Found' check: {result.error_message}")

    return False


async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    page_number: int,
    base_url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> Tuple[List[dict], bool]:
    """
    Fetches and processes a single page of venue data.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        page_number (int): The page number to fetch.
        base_url (str): The base URL of the website.
        css_selector (str): The CSS selector to target the content.
        llm_strategy (LLMExtractionStrategy): The LLM extraction strategy.
        session_id (str): The session identifier.
        required_keys (List[str]): List of required keys in the venue data.
        seen_names (Set[str]): Set of venue names that have already been seen.

    Returns:
        Tuple[List[dict], bool]:
            - List[dict]: A list of processed venues from the page.
            - bool: True if the "No Results Found" message was encountered, else False.
    """
    url = f"{base_url}?page={page_number}"
    print(f"Loading page {page_number}...")

    # Check for "No Results Found" before processing
    no_results = await check_no_results(crawler, url, session_id)
    if no_results:
        return [], True  # Signal to stop crawling

    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            css_selector=css_selector,
            session_id=session_id,
        ),
    )

    if not (result.success and result.extracted_content):
        print(f"Error fetching page {page_number}: {result.error_message}")
        return [], False

    # Debug: print raw extracted content
    print("Raw extracted content:", result.extracted_content)

    try:
        extracted_data = json.loads(result.extracted_content)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error on page {page_number}: {e}")
        return [], False

    if not extracted_data:
        print(f"No venues found on page {page_number}.")
        return [], False

    print("Extracted data:", extracted_data)

    complete_venues = []
    for venue in extracted_data:
        print("Processing venue:", venue)

        # Remove the 'error' key if it's False
        if venue.get("error") is False:
            venue.pop("error", None)

        if not is_complete_venue(venue, required_keys):
            print(f"Incomplete venue data for: {venue.get('name', 'Unknown')}")
            continue

        if is_duplicate_venue(venue["name"], seen_names):
            print(f"Duplicate venue '{venue['name']}' found. Skipping.")
            continue

        seen_names.add(venue["name"])
        complete_venues.append(venue)

    if not complete_venues:
        print(f"No complete venues found on page {page_number}.")
        return [], False

    print(f"Extracted {len(complete_venues)} venues from page {page_number}.")
    return complete_venues, False
