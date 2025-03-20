import os
import time
import random
import pandas as pd
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup

import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, WebDriverException

# Optional: webdriver-manager for auto-downloading ChromeDriver
try:
    from webdriver_manager.chrome import ChromeDriverManager
    AUTO_DOWNLOAD = True
except ImportError:
    AUTO_DOWNLOAD = False

# A small pool of user-agents to randomly choose from
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36 Edg/114.0.0.0",
]

def get_driver():
    """
    Creates an undetected-chromedriver instance with random user-agent,
    random window size, and extended timeouts.
    """
    user_agent = random.choice(USER_AGENTS)
    options = uc.ChromeOptions()

    # If you want to see the browser actions, comment out the headless argument:
    # options.add_argument("--headless=new")

    width = random.randint(1000, 1600)
    height = random.randint(700, 900)
    options.add_argument(f"--window-size={width},{height}")
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    if AUTO_DOWNLOAD:
        driver = uc.Chrome(
            driver_executable_path=ChromeDriverManager().install(),
            options=options,
        )
    else:
        driver = uc.Chrome(options=options)

    # Increase page load timeout as site can be slow or blocked
    driver.set_page_load_timeout(300)  # up to 5 minutes
    return driver

def scrape_draws(game, start_date, end_date, existing_dates):
    """
    Scrape draws for either 'Powerball' or 'Megamillions' from usamega.com,
    skipping dates outside [start_date, end_date],
    and skipping dates that already exist in 'existing_dates'.

    existing_dates: set of draw-date-strings in "MM/DD/YYYY" format we already have.

    Returns: list of dicts with columns:
        - Draw Date: "MM/DD/YYYY"
        - White Balls
        - Powerball (or MegaBall)
        - Jackpot
    """

    if game == "Powerball":
        base_url = "https://www.usamega.com/powerball/results/"
        table_selector = "table.results.pb tbody tr"
        next_link_fmt = "/powerball/results/{}"
        col_red = "Powerball"
    else:
        base_url = "https://www.usamega.com/mega-millions/results/"
        table_selector = "table.results.mm tbody tr"
        next_link_fmt = "/mega-millions/results/{}"
        col_red = "MegaBall"

    all_new_records = []
    driver = get_driver()

    page = 1
    try:
        while True:
            url = f"{base_url}{page}"
            print(f"[INFO] Loading page: {url}")

            # Attempt up to 3 retries for timeouts
            success = False
            for attempt in range(3):
                try:
                    driver.get(url)
                    success = True
                    break
                except TimeoutException:
                    print(f"[WARNING] Timeout on page {url}, attempt {attempt+1}. Retrying...")
                    time.sleep(3)
                except WebDriverException as e:
                    print(f"[ERROR] WebDriverException: {e}")
                    success = False
                    break

            if not success:
                print("[ERROR] Could not load page after retries. Stopping.")
                break

            # Sleep randomly so we don't look too bot-like
            time.sleep(random.uniform(2, 5))
            html = driver.page_source

            # Check for Cloudflare or blocking
            if any(block_str in html for block_str in ["cf-error-details", "Access Denied", "You have been blocked"]):
                print("[WARNING] Cloudflare or site block. Stopping.")
                break

            soup = BeautifulSoup(html, "html.parser")
            rows = soup.select(table_selector)
            if not rows:
                print(f"[INFO] No rows found on page {page}. Done scraping.")
                break

            found_any = False

            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) < 2:
                    continue

                section = tds[0].select_one("section.results")
                if not section:
                    continue

                date_a = section.find("a")
                if not date_a:
                    continue

                date_text = date_a.get_text(strip=True)  # e.g. "Wed, March, 19, 2025"
                parts = [p.strip() for p in date_text.split(",")]
                if len(parts) < 4:
                    continue
                # parse
                date_str_for_parse = f"{parts[1]} {parts[2]} {parts[3]}"
                try:
                    draw_dt = datetime.strptime(date_str_for_parse, "%B %d %Y").date()
                except ValueError:
                    continue

                # If outside user range, skip
                if draw_dt < start_date or draw_dt > end_date:
                    continue

                # Convert to "MM/DD/YYYY"
                draw_date_str = draw_dt.strftime("%m/%d/%Y")

                # If we already have this date, skip
                if draw_date_str in existing_dates:
                    continue

                ul = section.find("ul")
                if not ul:
                    continue

                lis = ul.find_all("li")
                white_balls = []
                red_ball = None
                for li in lis:
                    classes = li.get("class", [])
                    val = li.get_text(strip=True)
                    if "bonus" in classes:
                        red_ball = val
                    elif "multiplier" in classes:
                        pass
                    else:
                        white_balls.append(val)

                if len(white_balls) < 5 or not red_ball:
                    continue

                # jackpot in second <td>
                jackpot_a = tds[1].find("a")
                jackpot_str = jackpot_a.get_text(strip=True) if jackpot_a else ""

                record = {
                    "Draw Date": draw_date_str,
                    "White Balls": " ".join(white_balls[:5]),
                    col_red: red_ball,
                    "Jackpot": jackpot_str,
                }
                all_new_records.append(record)
                found_any = True

            if not found_any:
                print(f"[INFO] No valid draws on page {page}. Done scraping.")
                break

            # check next page link
            next_link = soup.select_one(f'a.button[href="{next_link_fmt.format(page+1)}"]')
            if next_link:
                time.sleep(random.uniform(2, 6))
                page += 1
            else:
                print("[INFO] No next page link found. Done scraping.")
                break

    finally:
        driver.quit()

    return all_new_records

def update_csv(game, csv_file, start_date, end_date):
    """
    Reads 'csv_file' if it exists, merges new data from scraping [start_date..end_date],
    then writes updated file.
    """
    if game == "Powerball":
        columns = ["Draw Date", "White Balls", "Powerball", "Jackpot"]
    else:
        columns = ["Draw Date", "White Balls", "MegaBall", "Jackpot"]

    if os.path.exists(csv_file):
        # read existing CSV
        old_df = pd.read_csv(csv_file, dtype=str)
        # Ensure columns exist
        for col in columns:
            if col not in old_df.columns:
                old_df[col] = ""
    else:
        old_df = pd.DataFrame(columns=columns)

    existing_dates = set(old_df["Draw Date"].fillna(""))

    # Scrape only missing draws in [start_date, end_date]
    new_records = scrape_draws(
        game=game,
        start_date=start_date,
        end_date=end_date,
        existing_dates=existing_dates
    )

    if not new_records:
        print("No new records found in that date range.")
        return

    new_df = pd.DataFrame(new_records)
    # Merge old + new
    merged_df = pd.concat([old_df, new_df], ignore_index=True)

    # Deduplicate by "Draw Date"
    merged_df.drop_duplicates(subset=["Draw Date"], keep="last", inplace=True)

    # Sort by date descending or ascending (your choice)
    def parse_dt(s):
        try:
            return datetime.strptime(s, "%m/%d/%Y")
        except:
            return None

    merged_df["parsed_date"] = merged_df["Draw Date"].apply(parse_dt)
    merged_df.sort_values(by="parsed_date", ascending=False, inplace=True)
    merged_df.drop(columns=["parsed_date"], inplace=True)

    # Save updated
    merged_df.to_csv(csv_file, index=False)
    print(f"[INFO] Updated {csv_file}. Total rows: {len(merged_df)}")

def main():
    # 1. Ask user for game
    game_choice = input("Enter 'Powerball' or 'Megamillions': ").strip()
    if game_choice not in ["Powerball", "Megamillions"]:
        print("Invalid choice, defaulting to Powerball.")
        game_choice = "Powerball"

    # 2. CSV filename
    if game_choice == "Powerball":
        csv_file = "powerball_results.csv"
    else:
        csv_file = "megamillions_results.csv"

    # 3. Ask user for date range in YYYY-MM-DD format
    start_str = input("Enter start date (YYYY-MM-DD): ")
    end_str = input("Enter end date   (YYYY-MM-DD): ")
    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date input. Defaulting to last 365 days.")
        end_dt = date.today()
        start_dt = end_dt - timedelta(days=365)

    if start_dt > end_dt:
        print("Swapping start/end because start > end.")
        start_dt, end_dt = end_dt, start_dt

    print(f"[INFO] Updating {game_choice} data from {start_dt} to {end_dt} in {csv_file}...")

    # 4. Update the CSV
    update_csv(game_choice, csv_file, start_dt, end_dt)

if __name__ == "__main__":
    main()
