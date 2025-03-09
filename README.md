# Crawler

This project is a web crawler built with Python that extracts venue data (wedding reception venues) from a website using asynchronous programming with Crawl4AI. It utilizes a language model-based extraction strategy and saves the collected data to a CSV file.

## Features

- Asynchronous web crawling using [Crawl4AI](https://pypi.org/project/Crawl4AI/)
- Data extraction powered by a language model (LLM)
- CSV export of extracted venue information
- Modular and easy-to-follow code structure ideal for beginners

## Project Structure
```
.
├── main.py # Main entry point for the crawler
├── config.py # Contains configuration constants (Base URL, CSS selectors, etc.)
├── models
│ └── venue.py # Defines the Venue data model using Pydantic
├── utils
│ ├── init.py # (Empty) Package marker for utils
│ ├── data_utils.py # Utility functions for processing and saving data
│ └── scraper_utils.py # Utility functions for configuring and running the crawler
├── requirements.txt # Python package dependencies
├── .gitignore # Git ignore file (e.g., excludes .env and CSV files)
└── README.MD # This file
```