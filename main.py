import time
import pandas as pd
from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import pywhatkit as kit

# Define the price limit and product name
PRICE_TARGET = 6400 # The limit price
PRODUCT_NAME = "samsung galaxy s24 ultra" # The product query
PHONE_NUMBER = "+40"  # Your phone number as +40712123123

# Initialize a new Chrome WebDriver

wd = wd.Chrome()
wd.maximize_window()
wd.implicitly_wait(10)

# Open the eMag website
search_website = "https://www.emag.ro/"
wd.get(search_website)
time.sleep(3)  # Wait for the page to load

# Searching for the specified product
searching_query = PRODUCT_NAME
search_bar_xpath = "/html//input[@id='searchboxTrigger']"
search_button_xpath = "/html//nav[@id='masthead']/div[@class='container']/div[@class='navbar-inner']//form[@action='/search']//i[@class='em em-search']"
search_bar_element = wd.find_element(By.XPATH, search_bar_xpath)
search_button_element = wd.find_element(By.XPATH, search_button_xpath)
search_bar_element.click()
time.sleep(0.2)
search_bar_element.send_keys(searching_query)
time.sleep(3)
search_button_element.click()
time.sleep(4)

# Parse the HTML content of the page using BeautifulSoup
soup = BeautifulSoup(wd.page_source, features="html.parser")


def getPandaDfForSearchResult(searchResultsPage):
    # Extract product information from search results
    time.sleep(4)
    rows = []  # pandas table
    for result in searchResultsPage:
        title = result.find("a", {"class": "card-v2-title"}).text
        price = result.find("p", {"class": "product-new-price"}).text
        link = result.find("a", {"class": "js-product-url"})["href"]
        row = [title, price, link]
        rows.append(row)

    # Create a DataFrame from the extracted data
    df = pd.DataFrame.from_records(rows, columns=["Title", "Price", "Link"])
    return df


def getSearchResultsForPages():
    # Aggregate search results from multiple pages
    df_all_search_results = pd.DataFrame(columns=["Title", "Price", "Link"])
    while True:
        searchResultsPage = soup.findAll("div", {"class": "card-item card-standard js-product-data"})
        df = getPandaDfForSearchResult(searchResultsPage)
        df_all_search_results = pd.concat([df_all_search_results, df])
        # Go to the next page
        try:
            next_button = wd.find_element(By.CLASS_NAME, "js-next-page")
            wd.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
        except StaleElementReferenceException:
            break
        except NoSuchElementException:
            break

    # Clean up price data and convert it to float
    df_all_search_results['Price'] = df_all_search_results['Price'].str.replace(" Lei", "").str.replace(".", "").str.replace(",", ".")
    df_all_search_results['Price'] = df_all_search_results['Price'].astype(float)
    return df_all_search_results


def sendWhatsAppMessage(df):
    # Send WhatsApp messages with product information and screenshots
    for index, graphicsCardRow in df.iterrows():
        print(graphicsCardRow.Link)
        wd.get(graphicsCardRow.Link)
        time.sleep(5)
        screenshotFilePath = f"C:/Users/George/Downloads/screenshot_{index}.png"
        wd.save_screenshot(screenshotFilePath)

        try:
            kit.sendwhats_image(PHONE_NUMBER, screenshotFilePath, graphicsCardRow.Link, wait_time=15, tab_close=True)
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            continue


# Main loop to search for the product and send messages if found
while True:
    df = getSearchResultsForPages()

    # Filter search results based on product name and price
    df_query = df[(df.Title.str.contains(PRODUCT_NAME, case=False)) & (df.Price <= PRICE_TARGET)]
    pd.set_option('display.max_columns', None)
    if not df_query.empty:
        print("I found a product")
        sendWhatsAppMessage(df_query)
        print(df_query)
        break
    else:
        break
