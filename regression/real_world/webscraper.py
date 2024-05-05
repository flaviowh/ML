
### A script to download housing sales data from OLX listings

import json
import requests
import bs4
import os
import concurrent.futures
import numpy as np


SAVING_FOLDER = os.path.join(os.path.join(
    os.environ['USERPROFILE']), 'Desktop')


MAIN_URL = "https://www.olx.com.br/imoveis/venda/estado-pb/paraiba/joao-pessoa?q=casa%20jo%C3%A3o%20pessoa&sd=4806&sd=4813&sd=4826&sd=4825&sd=4809&sd=4859&sd=4836&sd=4830&sd=4829&sd=4814&sd=4818&sd=4838&sd=4824&sd=4799&sd=4848&sd=4844&sd=4856&sd=4850&sd=4854&sd=4846&sd=4855&sd=4847&sd=4811&sd=4837&sd=4843&sd=4842&sd=4852&sd=4802&sd=4851&sd=4810&sd=4803&sd=4831&sd=4820&sd=4835&sd=4849&sd=4816&sd=4845&sd=4857&sd=4812&sd=4808&sd=4840&sd=4817&sd=4833&sd=4853&sd=4807&sd=4827&sd=4819&sd=4822&sd=4828&sd=4832&sd=4823&sd=4804&sd=4815&sd=4821&sd=4839&sd=4805&sd=4841&sd=4801&sd=4834&sd=4800&sd=4858"

LISTS_FOLDER = f"{SAVING_FOLDER}/lists"

children = range(1, 56)

DATA_FILE = f"{SAVING_FOLDER}/data.json"

LISTINGS_PER_PAGE = 50

VALIDATE = ["price", "area"]
USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}

#SELECTORS
LISTING_CHILD = '#main-content > div.sc-a8d048d5-2.prLrC > div:nth-child(+++)'
BEDROOMS = ' div > a > div > div.sc-12rk7z2-3.fqDYpJ > div.sc-12rk7z2-4.bGMpGA > div.sc-12rk7z2-5.fXzBqN > div.sc-12rk7z2-6.bmfccv > div > div > span:nth-child(1)'
AREA = '#content > div.ad__sc-18p038x-2.djeeke > div > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div.ad__duvuxf-0.ad__h3us20-0.eCUDNu > div.ad__h3us20-6.dHYhdu > div > div > div > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div:nth-child(5) > div > dd'
LOCATION = '#content > div.ad__sc-18p038x-2.djeeke > div > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div.ad__duvuxf-0.ad__h3us20-0.eCUDNu > div.ad__h3us20-6.eKoOwl > div > div > div > div.sc-hmzhuo.gqoVfS.sc-jTzLTM.iwtnNi > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div:nth-child(3) > div > dd'
PRICE = '#content > div.ad__sc-18p038x-2.djeeke > div > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div.ad__duvuxf-0.ad__h3us20-0.hwQusK > div.ad__h3us20-6.dcVYod > div > div > div.sc-cugefK.bYTZUF > div > h2.ad__sc-12l420o-1.cuGsvO.sc-drMfKT.fbofhg'
URL = ' div > a'
features = {"area": AREA,
            "bedrooms": BEDROOMS,
            "location": LOCATION,
            "price": PRICE}

FIRST_AD = '#ad-list > li.sc-1fcmfeb-2.iezWpY >'
LAST_AD = '#ad-list > li.sc-1fcmfeb-2.kZiBLm >'
CHILD = "#listing-pagination > aside > div > a:nth-child(+++)"

'#ad-list > li:nth-child(55) > div > a > div > div.sc-12rk7z2-3.fqDYpJ > div.sc-12rk7z2-4.bGMpGA > div.sc-12rk7z2-5.fXzBqN > div.sc-12rk7z2-6.bmfccv > div > div > span:nth-child(1)'


class DataScraper:
    def __init__(self) -> None:
        self.buffer = []

    def read_page(self, page):
        page_text = open(page, 'r', encoding='utf-8').read()
        entries = []

        first_prefix = FIRST_AD
        first_entry = self.get_features(first_prefix, page_text)
        entries.append(first_entry)

        last_prefix = LAST_AD
        last_entry = self.get_features(last_prefix, page_text)
        entries.append(last_entry)

        for n in children:
            prefix = CHILD.replace("+++", str(n))
            entry = self.get_features(prefix, page_text)
            entries.append(entry)

        self.buffer.append(entries)
        print("read page", page)


    def get_features(self, prefix, text):
        entry = {}
        for feature in features:
            sel = prefix + features[feature]
            entry[feature] = self.get_data_from_selector(text, sel)
        return entry


    def get_data_from_selector(self, text, selector):
        try:
            selector_str = selector
            bsp = bs4.BeautifulSoup(text, 'html.parser')
            data = bsp.select(selector_str)[0]
            return data.text
        except IndexError:
            pass


    def save_data(self, page):
        new_data = self.buffer
        file = f"{SAVING_FOLDER}/data.json"
        if os.path.isfile(file):
            old_file = open(file, "r", encoding='utf-8')
            previous_data = json.load(old_file)
        else:
            previous_data = ['']
        data = previous_data + new_data
        with open(file, "w", encoding='utf-8') as datafile:
            json.dump(data, datafile, indent=2, ensure_ascii=False)
            print("Data progress saved.")
        self.buffer.clear()
        with open(f"{SAVING_FOLDER}/to_read.json") as oldlist:
            previous_list = json.load(oldlist)
            previous_list.remove(page)
        with open(f"{SAVING_FOLDER}/to_read.json", 'w', encoding='utf-8') as newlist:
            json.dump(previous_list, newlist, indent=2, ensure_ascii=False)
            newlist.close()


    def run(self):
        read_file = f"{SAVING_FOLDER}/to_read.json"
        if not os.path.isfile(read_file):
            with open(f"{SAVING_FOLDER}/to_read.json", "w", encoding="utf-8") as output:
                files = [os.path.join(LISTS_FOLDER, f) for f in os.listdir(LISTS_FOLDER) if f.endswith(".html")]
                json.dump(files, output)
                output.close()

        while True:
            with open(read_file, 'r', encoding='utf-8') as f:
                LISTS = json.load(f)
                print(len(LISTS), "lists to read.")
                page = LISTS[0]
                self.read_page(page)
                self.save_data(page)

######### ________________________________________________________

class LinkScraper:
    """Gets the OLX pages and the links for scraping"""

    def __init__(self, max_lists=100):
        self.buffer = []
        self.max_lists = max_lists

    def get_links_list(self):
        self.get_listing_pages()
        self.download_links_from_pages()

    def download_links_from_pages(self):
        if not self.links_list_exists():
            lists_folder = f"{SAVING_FOLDER}/lists"
            listing_pages = [os.path.join(lists_folder, page) for page in os.listdir(
                lists_folder) if page.endswith(".html")]
            print("Downloading the links...")
            with concurrent.futures.ThreadPoolExecutor() as link_readers:
                link_readers.map(self.get_page_links, listing_pages)

            if not len(self.buffer):
                print("Error: buffer is empty")
                return

            links_file = f"{SAVING_FOLDER}/all_links.txt"
            complete_list = list(np.concatenate(self.buffer).flat)
            with open(links_file, 'w', encoding='utf-8') as output:
                for link in complete_list:
                    output.write(f"{link}\n")
                output.close()
            self.buffer.clear()
            print("The list of links is ready.\n")
        else:
            print("The links list file already exists.")


    def links_list_exists(self):
        return True if os.path.isfile(f"{SAVING_FOLDER}/all_links.txt") else False

    def get_page_links(self, html_file):
        page_text = open(html_file, 'r', encoding='utf-8').read()
        links = set()
        bsp = bs4.BeautifulSoup(page_text, 'html.parser')
        for n in range(1, LISTINGS_PER_PAGE):
            try:
                ad = str(bsp.select(LISTING_CHILD.replace("+++", str(n)))[0])
                bsp2 = bs4.BeautifulSoup(ad, 'html.parser')
                for link in bsp2.find_all('a'):
                    address = link.get('href')
                    links.add(address)
            except IndexError:
                continue

        if len(links):
            print(f"got {len(links)} links\n")
            self.buffer.append(list(links))
        else:
            raise Exception(
                "Error. No links found in the list page. Check the selectors.")

    def get_listing_pages(self):
        lists_folder = f'{SAVING_FOLDER}/lists'
        os.makedirs(lists_folder, exist_ok=True)
        print("\n downlading the lists of links...")
        lists_folder = rf'{SAVING_FOLDER}/lists'
        lists_downloaded = [os.path.join(lists_folder, file) for file in os.listdir(
            lists_folder) if file.endswith(".html")]

        if not len(lists_downloaded):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(self.get_listing_page, range(1, self.max_lists + 1))
            return

        print(f"{len(lists_downloaded)} listing pages ready")
        return

    def get_listing_page(self, page_num):
        output_file = rf'{SAVING_FOLDER}/lists/list_page{page_num}.html'
        if os.path.isfile(output_file):
            return

        page_url = MAIN_URL.replace("+++", str(page_num))
        req = requests.get(page_url, headers=USER_AGENT)
        if req.status_code == 200:
            with open(output_file, 'w', encoding='utf-8') as output:
                output.write(req.text)
                print(f"\ndownloaded listing page {page_num}")
        else:
            raise Exception(
                f"Error. Received status code {req.status_code} getting listing page {page_num}")
        return


if __name__ == "__main__":
    linksScraper = LinkScraper(200)
    linksScraper.get_links_list()
    # datascraper = DataScraper()
    # datascraper.run()

# with open(f"{SAVING_FOLDER}/to_read.json", 'r', encoding='utf-8') as f:
#     lista = json.load(f)
#     print(len(lista))
