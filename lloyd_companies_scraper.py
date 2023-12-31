import requests
from bs4 import BeautifulSoup
from time import sleep
from collections import namedtuple
import pandas as pd
import string
import json
import os

ORIGIN_URL = "https://directories.lloydslist.com/company-browse-name/searchid/0/searchchar/"
BASE_URL = "https://directories.lloydslist.com/var/recordset/66203/pos/"

headers = {
    'User-Agent':
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'Cookie':
      'SESSID=fvcnmhcuop3k39eiv86kseh1o6; _ga=GA1.2.441504706.1651317015; _gid=GA1.2.1133239103.1651317015; dismissedBanners={%22cookie-policy-0001%22:true}; _gat=1'
    }

FIELDS = ['Name', 'Address', 'Telephone', 'Email','Vessels owned', 'URL', 'lloyd url']

DIR_PATH = f"{os.getcwd()}/drive/MyDrive/LLoyd Data/Companies/"
OUTPUT_FILEPATH = DIR_PATH + 'All_Companies.xlsx'
METADATA_FILEPATH = DIR_PATH + 'metadata.json'

def dump_json(dict, filepath):
  with open(filepath, 'w') as json_file:
    json.dump(dict, json_file, indent=4)

def load_json(filepath):
  with open(filepath) as file:
    dict = json.load(file)

  return dict

def save_data_to_drive(data, filepath):
  df = pd.DataFrame(data)
  df.to_excel(filepath, index=None)
  print(f"******** Data saved successfully to {filepath} **********")

def parse_soup(url):
  r = requests.get(url, headers=headers)

  if (r.ok):
    soup = BeautifulSoup(r.text, 'lxml')
    return soup

def get_pages_and_listings(soup):
  page_div = soup.find('div', class_='page-counter')
  pages = page_div.getText().strip().split('of ')[-1]

  listing_div = soup.find('div', class_='list-counter')
  listings = listing_div.getText().strip().split('of ')[-1]

  return int(pages), int(listings)

def save_metadata(filepath):
  metadata = {}

  for alphabet in string.ascii_uppercase:
    url = ORIGIN_URL + alphabet

    soup = parse_soup(url)
    sleep(0.1)

    pages, listings = get_pages_and_listings(soup)
    metadata[alphabet] = {'pages':pages, 'listings':listings}

  dump_json(metadata, filepath)
  print(f"********** Metadata saved successfully to {filepath} ************")

def load_metadata(filepath):
  metadata = load_json(filepath)
  print(f"********** Metadata loaded successfully from {filepath} ************")

  Count = namedtuple('Count', ['pages', 'listings'])
  for key, value in metadata.items():
    metadata[key] = Count(**value)

  return metadata

metadata = load_metadata(METADATA_FILEPATH)

def get_table_rows(soup):
  page_title = soup.title.text.strip()
  fethed_alphabet = soup.find('div', class_='sectionhead').text
  fetched_pageNo = soup.find(id='pagingCurrent').a.text

  print(f"Scraping Data (Alphabet: {fethed_alphabet}, Actual PageNo: {fetched_pageNo}).......")

  # Get table and all its data rows
  table = soup.find('table', class_='tf-66253')
  table_rows = table.find_all('tr')

  return table_rows

def get_name(row):
  return row.td.p.getText().strip()

def get_address(row):
  return row.td.p.getText().strip()

def get_contact(row):
  text = row.td.getText()

  if (text == " "): return "", ""

  contact = text.split(" | ")

  # If only telephone present
  if (len(contact) == 1):
    tel = contact[0][5:].strip()
    return "", tel

  tel = contact[0][5:] # parse telephone
  email = contact[1][7:] # parse email

  return email, tel

def get_vessels_and_url(row):
  details = list(row.td.children)

  url = details[0].a.getText()
  lloyd_url = "https://directories.lloydslist.com" + details[1].a['href']

  dl =  details[1].a.getText().strip()
  vessels_owned = dl.split('(')[-1].split(' ')[0]

  return url, lloyd_url, vessels_owned

def insert_records(records_cache, table_rows):
  n = 0
  print("Inserting records......")

  for i in range(len(table_rows)):
    row = table_rows[i]

    if (i % 4 == 0):
      record = {}
      record[FIELDS[0]] = get_name(row)

    elif (i % 4 == 1):
      record[FIELDS[1]] = get_address(row)

    elif (i % 4 == 2):
      email, tel = get_contact(row)

      record[FIELDS[2]] = tel
      record[FIELDS[3]] = email

    elif (i % 4 == 3):
      url, lloyd_url, vessels_owned = get_vessels_and_url(row)

      record[FIELDS[4]] = vessels_owned
      record[FIELDS[5]] = url
      record[FIELDS[6]] = lloyd_url

      # Save record object to cache
      records_cache.append(record)
      n += 1

  return n

def scrape_data(alphabet, Count, page=None):
  total_pages = Count.pages
  main_url = ORIGIN_URL + alphabet

  data = []

  r = requests.get(main_url, headers=headers)
  if (r.ok):
    print(f"Main request successful (Alphabet: {alphabet}, Total Pages={total_pages}) \n")

  records_inserted = 0

  for p in range(total_pages):

    # Skip If page provided and p is not equal to page
    if (page and p != page-1):
       continue

    page_no = (p*10)+1
    url = BASE_URL + str(page_no)

    sleep(0.1)
    soup = parse_soup(url)
    print(f"Parsed soup (Alphabet: {alphabet}, Provided PageNo: {page_no})")

    table = get_table_rows(soup)
    records = insert_records(data, table)

    records_inserted += records
    print('-----------------------------------------------------')

  return data, records_inserted

def test_scrape(alphabet, Count, page=None):
  total_pages = Count.pages

  if page:
    print(f"Testing Insertion for Alphabet {alphabet}, Page No. - {page}")

  else:
    print(f"Testing Insertion for Alphabet {alphabet}, total pages - {total_pages}")

  data, rows_inserted = scrape_data(alphabet, Count, page)

  if page:
    print(f"************* Scrape Test passed (Alphabet: {alphabet}, Page:{page}) ***************\n")

  else:
    if (rows_inserted / total_pages >= 9):
      print(f"*********** Scrape Test Passed for Alphabet - {alphabet} *************\n")
    else:
      print(f"*********** Scrape Test Failed for Alphabet - {alphabet} *************\n")

  return data

test_alpha = 'S'
test_data = test_scrape(test_alpha, metadata[test_alpha], 2)

def scrape_all_pages(alphabet_list):
  try:
    final_data = []
    for alphabet, Count in metadata.items():
      if alphabet not in alphabet_list:
        continue

      data, records_inserted = scrape_data(alphabet, Count)
      final_data += data

      if (records_inserted == Count.listings):
        print(f"\n******************* ALPHABET {alphabet} completed - All Records inserted: {records_inserted} :) **********************")

      else:
        print(f"\n!!!!!!!!!!!!!!!!!!! ALPHABET {alphabet} completed - Records missed: {Count.listings - records_inserted} :( !!!!!!!!!!!!!!!!!!!!!!")

  except Exception as E:
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!! Exception: {E} !!!!!!!!!!!!!!!!!!!!!!!!!!!!")

  finally:
    return final_data

alphabet_list = string.ascii_uppercase
final_data = scrape_all_pages(alphabet_list)
df = pd.DataFrame(final_data)
