# Lottery Draw Scraper

This Python script scrapes lottery draw results (Powerball or Mega Millions) from [usamega.com](https://www.usamega.com) and saves them to a CSV file. It uses Selenium with undetected-chromedriver to avoid detection and BeautifulSoup for parsing HTML.

---

## Features

- **Scrapes Lottery Results**: Fetches Powerball or Mega Millions draw results from [usamega.com](https://www.usamega.com).
- **Date Range Filtering**: Allows you to specify a date range for scraping.
- **CSV Updates**: Merges new results with existing data in a CSV file, avoiding duplicates.
- **Randomized User-Agent**: Uses a random user-agent and window size to avoid detection.
- **Retry Mechanism**: Retries failed requests up to 3 times.
- **Cloudflare Detection**: Stops scraping if Cloudflare or site blocking is detected.

---

## Requirements

- **Python 3.11**: This script requires Python 3.11 due to library dependencies.
- **Libraries**:
  - `selenium`
  - `undetected-chromedriver`
  - `beautifulsoup4`
  - `pandas`
  - `webdriver-manager` (optional, for automatic ChromeDriver installation)

---

## Installation

1. **Install Python 3.11**:
   - Download and install Python 3.11 from [python.org](https://www.python.org/downloads/).

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python3.11 -m venv lottery-env
   source lottery-env/bin/activate  # On Windows, use `lottery-env\Scripts\activate`
   ```

3. **Install Required Libraries**:
   ```bash
   pip install selenium undetected-chromedriver beautifulsoup4 pandas webdriver-manager
   ```

4. **Download ChromeDriver** (if not using `webdriver-manager`):
   - Ensure you have Google Chrome installed.
   - Download the matching version of ChromeDriver from [here](https://sites.google.com/chromium.org/driver/).

---

## Usage

1. **Run the Script**:
   ```bash
   python lottery_scraper.py
   ```

2. **Follow the Prompts**:
   - Enter the lottery game (`Powerball` or `Megamillions`).
   - Specify the start and end dates in `YYYY-MM-DD` format.
   - The script will scrape the results and save them to a CSV file (`powerball_results.csv` or `megamillions_results.csv`).

3. **Output**:
   - The CSV file will contain the following columns:
     - `Draw Date`: Date of the draw in `MM/DD/YYYY` format.
     - `White Balls`: The winning white ball numbers.
     - `Powerball` or `MegaBall`: The winning red ball number.
     - `Jackpot`: The jackpot amount.

---

## Example

```bash
$ python lottery_scraper.py
Enter 'Powerball' or 'Megamillions': Powerball
Enter start date (YYYY-MM-DD): 2023-01-01
Enter end date   (YYYY-MM-DD): 2023-10-01
[INFO] Updating Powerball data from 2023-01-01 to 2023-10-01 in powerball_results.csv...
[INFO] Loading page: https://www.usamega.com/powerball/results/1
[INFO] Updated powerball_results.csv. Total rows: 100
```

---

## Functions

### `get_driver()`
- Creates an undetected ChromeDriver instance with a random user-agent and window size.
- Configures options to avoid detection (e.g., disables automation features).

### `scrape_draws(game, start_date, end_date, existing_dates)`
- Scrapes lottery results for the specified game (`Powerball` or `Megamillions`) within the given date range.
- Skips dates already present in `existing_dates`.
- Returns a list of dictionaries containing draw results.

### `update_csv(game, csv_file, start_date, end_date)`
- Reads an existing CSV file (if any), merges new results, and saves the updated data.
- Ensures no duplicate entries based on the draw date.

### `main()`
- Handles user input (game choice, date range) and initiates the scraping process.

---

## Notes

- **Cloudflare Blocking**: If the script detects Cloudflare or site blocking, it will stop scraping. You may need to wait before running it again.
- **Headless Mode**: By default, the browser runs in headless mode. To see the browser actions, uncomment the `--headless=new` argument in `get_driver()`.
- **Date Range**: If no valid date range is provided, the script defaults to the last 365 days.

---

## License

This project is open-source and available under the MIT License. Feel free to modify and distribute it as needed.
