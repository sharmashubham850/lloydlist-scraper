import requests
from bs4 import BeautifulSoup
from time import sleep

class CompaniesScraper:
  ORIGIN_URL = "https://directories.lloydslist.com/company-browse-name/searchid/0/searchchar/"
  BASE_URL = "https://directories.lloydslist.com/var/recordset/66203/pos/"

  def scrape_companies(self, alphabet, pageNo):
    url1 = self.ORIGIN_URL + alphabet
    url2 = self.BASE_URL + str(pageNo)
    
    headers = {
    'User-Agent': 
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'Cookie': 
      'SESSID=fvcnmhcuop3k39eiv86kseh1o6; _ga=GA1.2.441504706.1651317015; _gid=GA1.2.1133239103.1651317015; dismissedBanners={%22cookie-policy-0001%22:true}; _gat=1'
    }


    r1 = requests.get(url1, headers=headers)
    sleep(0.2)
    r2 = requests.get(url2, headers=headers)
    
    if (not r2.ok):
      print("Request failed")
      return []

    soup = BeautifulSoup(r2.text, 'lxml')
    print(soup.title.text)

    fethed_alphabet = soup.find('div', class_='sectionhead').text
    print(fethed_alphabet)
    print('Alphabet Verification-', alphabet == fethed_alphabet)

    # Get table and all its data rows
    table = soup.find('table', class_='tf-66253')
    table_rows = table.find_all('tr')





  def get_name(self, row):
    


if __name__ == "__main__":
  scraper = CompaniesScraper()
  scraper.scrape_companies(alphabet='D', pageNo=1)