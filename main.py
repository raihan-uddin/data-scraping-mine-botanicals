import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re


# Function to fetch all collections (categories) from the main collections page
def fetch_collections(base_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    collections = []
    collection_list = soup.find_all('div', class_='collection-grid-item')

    for collection in collection_list:
        try:
            collection_link = collection.find('a', class_='collection-grid-item__link')['href']
            collection_title = collection.find('div', class_='collection-grid-item__title').text.strip()
            collections.append({
                'Title': collection_title,
                'URL': f"https://minebotanicals.com{collection_link}"
            })
        except Exception as e:
            print(f"Error processing collection: {e}")

    return collections


# Function to fetch product list from a collection page with pagination
def fetch_products(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    products = []
    product_list = soup.find_all('div', class_='item-product')
    for product in product_list:
        try:
            product_link = product.find('a')['href']
            # get product details
            product_details = fetch_product_details(f"https://minebotanicals.com{product_link}")
            if product_details:
                products.append(product_details)

            # print(product_details)
        except Exception as e:
            print(f"Error processing product: {e}")
    return products


# Function to fetch product details from a product page
def fetch_product_details(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    product_details = {}
    #
    # Find all script tags
    script_tags = soup.find_all('script')
    # Loop through script tags to find the one containing json_product
    json_product_data = None
    for script in script_tags:
        if 'var json_product =' in script.text:
            # Use regex to extract JSON part of the script
            json_text = re.search(r'var json_product = ({.*});', script.text).group(1)
            json_product_data = json.loads(json_text)
            break
    # Extract product details from json_product_data
    product_details['title'] = json_product_data.get('title', '')
    product_details['description'] = json_product_data.get('description', '')
    product_details['vendor'] = json_product_data.get('vendor', '')
    product_details['type'] = json_product_data.get('type', '')

    categories = [link.get_text(strip=True).rstrip(',') for link in
              soup.find('p', itemprop='cat', class_='product-single__cat').find_all('a')]

    product_details['categories'] = categories
    product_details['tags'] = json_product_data.get('tags', [])
    product_details['price'] = f"{json_product_data.get('price', 0) / 100:.2f}"
    product_details['price_min'] = f"{json_product_data.get('price_min', 0) / 100:.2f}"
    product_details['price_max'] = f"{json_product_data.get('price_max', 0) / 100:.2f}"
    variants = json_product_data.get('variants', [])
    # only keep the necessary fields from variants i.e title, sku, public_title, options, price, weight
    variants_data = [{'title': variant.get('title', ''),
                      'sku': variant.get('sku', ''),
                      'public_title': variant.get('public_title', ''),
                      'options': variant.get('options', ''),
                      'price': f"{variant.get('price', 0) / 100:.2f}",
                      'weight': variant.get('weight', '')} for variant in variants]
    product_details['variants'] = variants_data
    product_details['images'] = json_product_data.get('images', [])
    product_details['featured_image'] = json_product_data.get('featured_image', '')
    product_details['content'] = json_product_data.get('content', '')

    return product_details


# Function to iterate through paginated pages within a collection
def scrape_collection(collection_url):
    all_products = []
    page_number = 1
    while True:
        print("------------------------------------------------")
        collection_start_time = time.time()
        print(f"Collection scraping started at {time.ctime()}")
        url = f"{collection_url}?page={page_number}"
        print(f"Scraping page {page_number} of collection: {url}")

        products = fetch_products(url)
        if not products:
            break
        all_products.extend(products)
        page_number += 1
        time.sleep(2)  # Respectful delay to avoid hammering the server
        print(f"Total products scraped from page {page_number - 1}: {len(products)}")

    print(f"Total products scraped from collection: {len(all_products)}")
    print(f"Time taken to scrape collection {collection_url}: {time.time() - collection_start_time:.2f} seconds")
    return all_products


# Main function to scrape all collections and their products
def main():
    start_time = time.time()
    print(f"Starting scraping at {time.ctime()}")
    base_url = 'https://minebotanicals.com/collections'

    # Step 1: Fetch all collections
    collections = fetch_collections(base_url)

    # Step 2: Scrape products for each collection
    all_data = []
    for collection in collections:
        print(f"Scraping collection: {collection['Title']} ({collection['URL']})")
        collection_products = scrape_collection(collection['URL'])
        all_data.extend(collection_products)

    print(f"Total products scraped: {len(all_data)}")

    print(f"Time taken: {time.time() - start_time:.2f} seconds")

    # Save to excel file
    df = pd.DataFrame(all_data)
    df.to_excel('minebotanicals_products.xlsx', index=False)
    print("Data saved to minebotanicals_products.xlsx")
    print(f"Time taken: {time.time() - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
