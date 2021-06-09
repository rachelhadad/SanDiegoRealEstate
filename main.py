from map import show_graph
import os
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import sqlite3
import datetime
import re
import time

con = sqlite3.connect('sandiegorealestate.db')
cur = con.cursor()
today = datetime.date.today()

DRIVER_PATH = os.environ.get("chrome_driver_path")
driver = webdriver.Chrome(executable_path=DRIVER_PATH)
actions = ActionChains(driver)
filter_criteria = "/filter/property-type=house,min-beds=3,min-baths=2,min-sqft=3k-sqft,status=active"
cities = [ {"name": "Carlsbad",
            "all_url": "https://www.redfin.com/city/2891/CA/Carlsbad/filter/status=active",
            "filtered_url": f"https://www.redfin.com/city/2891/CA/Carlsbad{filter_criteria}"},
            {"name": "Del-Mar",
            "all_url": "https://www.redfin.com/city/4792/CA/Del-Mar/filter/status=active",
            "filtered_url": f"https://www.redfin.com/city/4792/CA/Del-Mar{filter_criteria}"},
            {"name": "Solana-Beach",
            "all_url": "https://www.redfin.com/city/18500/CA/Solana-Beach/filter/status=active",
            "filtered_url": f"https://www.redfin.com/city/18500/CA/Solana-Beach{filter_criteria}"},
            {"name": "Encinitas",
            "all_url": "https://www.redfin.com/city/5844/CA/Encinitas/filter/status=active",
            "filtered_url": f"https://www.redfin.com/city/5844/CA/Encinitas{filter_criteria}"},
            {"name": "Carmel-Valley",
            "all_url": "https://www.redfin.com/neighborhood/371/CA/San-Diego/Carmel-Valley/filter/status=active",
            "filtered_url": f"https://www.redfin.com/neighborhood/371/CA/San-Diego/Carmel-Valley{filter_criteria}"}
        ]

def get_num_of_houses():
    num_of_houses_string = driver.find_element_by_class_name("description").text
    # Try/Except in case results are only 1 page, bc results are listed differently than if there are multiple pages
    try:
        num_of_houses = re.search("(of\s)(\d+)", num_of_houses_string)[2]
    except TypeError:
        num_of_houses = re.search("\d+", num_of_houses_string)[0]
    finally:
        num_of_houses = int(num_of_houses)
    return num_of_houses

def get_listings(driver_url, all_table_name, city):
    driver.get(driver_url)
    driver.maximize_window()
    num_of_houses = get_num_of_houses()
    # list price and sq ft are at different driver locations. So, use for loop to assign driver find location depending on MapHomeCard number
    for n in range(0, num_of_houses - 1):
        if n < 82:
            # Selenium is struggling with stale arguments/no such arguments (even though they do exist at the provided location), so just pass at these errors and keep going
            # TODO why is Selenium struggling?
            try:
                get_list_price = driver.find_element_by_css_selector(f"#MapHomeCard_{n} > div > div > div.bottomV2 > span").text
                get_sq_ft = driver.find_element_by_css_selector(f"#MapHomeCard_{n} > div > div > div.bottomV2 > div.HomeStatsV2.font-size-small > div:nth-child(3)").text
            except NoSuchElementException:
                pass
        elif n > 82:
            try:
                get_list_price = driver.find_element_by_xpath(f"//*[@id='MapHomeCard_{n}']/div/div/div[2]/span").text
                get_sq_ft = driver.find_element_by_xpath(f"//*[@id='MapHomeCard_{n}']/div/div/div[2]/div[2]/div[3]").text
            except NoSuchElementException:
                pass

        # convert list price to int
        numeric_filter = filter(str.isdigit, get_list_price)
        numeric_string = "".join(numeric_filter)
        list_price = int(numeric_string)

        # Convert sq. ft. to int
        split_sq_ft = get_sq_ft.replace(',', '').split()
        if re.search(r"^\D+", split_sq_ft[0]):
            print("Not a valid sq. ftg.")
            pass
        else:
            clean_sq_ft = float(split_sq_ft[0])
            if split_sq_ft[1] == 'Sq.':
                sq_ft = clean_sq_ft
            elif split_sq_ft[1] == 'Acres':
                sq_ft = round(clean_sq_ft * 43560)
            pricepersqft = round(list_price / sq_ft, 2)
            cur.execute(f"INSERT INTO {all_table_name} (date, city, listing_price, sq_ft, price_per_sq_ft) VALUES (?, ?, ?, ?, ?)", (today, city, list_price, sq_ft, pricepersqft,))
            print(f"Added {n}")
        # Go to next page; the first page goes to 40 and the rest to 41, so the if math equation determins when to go to next page
        if (n - 40) % 41 == 0:
            try:
                next_page_button = driver.find_element_by_css_selector(r"#results-display > div:nth-child(7) > div > div > div.PagingControls > button:nth-child(3)")
                time.sleep(2)
                actions.move_to_element(next_page_button).perform()
                time.sleep(1)
                next_page_button.click()
                print("Went to next page.")
            except StaleElementReferenceException:
                current_url = driver.current_url
                url_regex=re.search(r"(status=active)(.*)($)", current_url)
                if url_regex[2]:
                    page_number = current_url[len(current_url) - 1]
                    url_slice = current_url[:-1]
                    new_url = url_slice + str((int(page_number) + 1))
                    driver.get(new_url)
                else:
                    new_url = current_url + "/page-2"
            finally:
                time.sleep(2)
        else:
            pass

def get_averages(driver_url, from_table_name, averages_table_name, city):
    num_of_houses = get_num_of_houses()
    driver.get(driver_url)

    # Get and format data
    get_avg_listing_price = cur.execute(f"SELECT avg(listing_price) FROM {from_table_name} WHERE date = ?", (today,))
    avg_listing_price = round(get_avg_listing_price.fetchone()[0])
    get_avg_sq_ft = cur.execute(f"SELECT avg(sq_ft) FROM {from_table_name} WHERE date = ?", (today,))
    avg_sq_ft = round(get_avg_sq_ft.fetchone()[0],2)
    get_avg_ppsqft = cur.execute(f"SELECT avg(price_per_sq_ft) FROM {from_table_name} WHERE date = ?", (today,))
    avg_ppsqft = round(get_avg_ppsqft.fetchone()[0], 2)

    cur.execute(f"INSERT INTO {averages_table_name} (date, city, total_listings, listing_price, sq_ft, price_per_sq_ft) VALUES (?, ?, ?, ?, ?, ?)", (today, city, num_of_houses, avg_listing_price, avg_sq_ft, avg_ppsqft,))
    con.commit()

    # Print data to console
    fetch_listing_price = cur.execute(f"SELECT listing_price FROM {averages_table_name} WHERE date = ?", (today,))
    price_data = fetch_listing_price.fetchall()
    print("Average listing price for " + city.replace("-", " ") + " in " + averages_table_name + ": ${:,}".format(price_data[0][0]))
    fetch_sqft = cur.execute("SELECT price_per_sq_ft FROM averages WHERE date = ?", (today,))
    sqft_data = fetch_sqft.fetchall()
    print("Average price per sqft for " + city.replace("-", " ") + " in " + averages_table_name + ": {0:,.2f}".format(sqft_data[0][0]) + " sq. ft.")

# Call functions for each city in cities dictionary
# Sleep allows pages to load between function calls
for city in cities:
    print(city["name"])
    get_listings(city["all_url"], "all_listings", city["name"])
    time.sleep(2)
    get_listings(city["filtered_url"], "my_listings", city["name"])
    time.sleep(2)
    get_averages(city["all_url"], "all_listings", "averages", city["name"])
    time.sleep(2)
    get_averages(city["filtered_url"], "my_listings", "my_averages", city["name"])

show_graph()
con.close()
