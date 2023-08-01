# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from time import sleep
from collections import namedtuple
import pandas as pd
import string
import json
import os

ORIGIN_URL = "https://directories.lloydslist.com/company-browse-vessel/searchid/0/searchchar/"
BASE_URL = "https://directories.lloydslist.com/var/recordset/66333/pos/"

old = {'Cookie':
      'SESSID=fvcnmhcuop3k39eiv86kseh1o6; _ga=GA1.2.441504706.1651317015; _gid=GA1.2.1133239103.1651317015; dismissedBanners={%22cookie-policy-0001%22:true}; _gat=1'}
headers = {
    'User-Agent':
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
      'Cookie':'dismissedBanners={%22cookie-policy-0001%22:true}; _ga=GA1.2.69827270.1651949490; _gid=GA1.2.349393032.1651949490; _gat=1; SESSID=p01jip0pe9p2s063hbafs01cr7'
    }

FIELDS = ['Name', 'Manager', 'Type', 'Owner Name', 'Owner ID']

DIR_PATH = f"{os.getcwd()}/LLoyd Data/Vessels/"

TEST_OUTPUT_FILEPATH = DIR_PATH + 'Vessel_Q.xlsx'
OUTPUT_FILEPATH = DIR_PATH + 'All_Vessels.xlsx'
METADATA_FILEPATH = DIR_PATH + 'metadata.json'

def dump_json(dict, filepath):
  with open(filepath, 'w') as json_file:
    json.dump(dict, json_file, indent=4)

def load_json(filepath):
  with open(filepath) as file:
    dict = json.load(file)

  return dict

def save_data_to_file(data, filepath):
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
  table = soup.find('table', class_='tf-66303')
  table_rows = table.find_all('tr')

  return table_rows

# Vessel Name
def get_name(row):
  return row.td.p.getText().strip().upper()

# Vessel Manager
def get_manager(row):
  return row.td.getText().strip()

# Vessel Type
def get_type(row):
  return row.td.getText().strip()

# Owner name and id
def get_owner(row):
  a_tag = row.td.p.a

  id = a_tag['href'].split('/')[3]

  name_text = a_tag.getText().strip()
  name = ' '.join(name_text.split(' ')[:-2])

  return id, name

def insert_records(records_cache, table_rows):
  n = 0
  print("Inserting records......")

  for i in range(len(table_rows)):
    row = table_rows[i]

    if (i % 5 == 0):
      record = {}
      record[FIELDS[0]] = get_name(row)

    elif (i % 5 == 1):
      record[FIELDS[1]] = get_manager(row)

    elif (i % 5 == 2):
      record[FIELDS[2]] = get_type(row)

    elif (i % 5 == 4):
      owner_id, owner_name = get_owner(row)

      record[FIELDS[3]] = owner_name
      record[FIELDS[4]] = owner_id

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
final_data = scrape_all_pages(alphabet_list=alphabet_list)
df = pd.DataFrame(final_data)

save_data_to_file(final_data, TEST_OUTPUT_FILEPATH)

