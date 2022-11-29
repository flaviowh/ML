import json
import requests
import bs4
import os
import concurrent.futures
import numpy as np


"""An old script to download housing sales data from OLX listings
 as of 11/2022 the selectors are outdated
"""

# CHANGE THESE DEPENDING ON PROJECT
SAVING_FOLDER = os.path.join(os.path.join(
    os.environ['USERPROFILE']), 'Desktop')


MAIN_URL = "https://pb.olx.com.br/paraiba/joao-pessoa/imoveis/venda?o=+++&q=casas%20jo%C3%A3o%20pessoa"

CHILD_LINK = "#ad-list > li:nth-child(+++)"

LISTS_FOLDER = f"{SAVING_FOLDER}/lists"

children = range(1, 56)

DATA_FILE = f"{SAVING_FOLDER}\DATA.json"

# NEED TO UPDATE THESE 
BEDROOMS = ' div > a > div > div.sc-12rk7z2-3.fqDYpJ > div.sc-12rk7z2-4.bGMpGA > div.sc-12rk7z2-5.fXzBqN > div.sc-12rk7z2-6.bmfccv > div > div > span:nth-child(1)'
AREA = '#content > div.ad__sc-18p038x-2.djeeke > div > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div.ad__duvuxf-0.ad__h3us20-0.eCUDNu > div.ad__h3us20-6.dHYhdu > div > div > div > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div:nth-child(5) > div > dd'
LOCATION = '#content > div.ad__sc-18p038x-2.djeeke > div > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div.ad__duvuxf-0.ad__h3us20-0.eCUDNu > div.ad__h3us20-6.eKoOwl > div > div > div > div.sc-hmzhuo.gqoVfS.sc-jTzLTM.iwtnNi > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div:nth-child(3) > div > dd'
PRICE = '#content > div.ad__sc-18p038x-2.djeeke > div > div.sc-bwzfXH.ad__h3us20-0.ikHgMx > div.ad__duvuxf-0.ad__h3us20-0.hwQusK > div.ad__h3us20-6.dcVYod > div > div > div.sc-cugefK.bYTZUF > div > h2.ad__sc-12l420o-1.cuGsvO.sc-drMfKT.fbofhg'
URL = ' div > a'
VALIDATE = ["price", "area"]
USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}

features = {"area": AREA, "bedrooms": BEDROOMS,
            "location": LOCATION, "price": PRICE}

FIRST_AD = '#ad-list > li.sc-1fcmfeb-2.iezWpY >'
LAST_AD = '#ad-list > li.sc-1fcmfeb-2.kZiBLm >'
CHILD = '#ad-list > li:nth-child(+++) >'

'#ad-list > li:nth-child(55) > div > a > div > div.sc-12rk7z2-3.fqDYpJ > div.sc-12rk7z2-4.bGMpGA > div.sc-12rk7z2-5.fXzBqN > div.sc-12rk7z2-6.bmfccv > div > div > span:nth-child(1)'

CACHE = []

class DataScraper:
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

        CACHE.append(entries)
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
        new_data = CACHE
        file = f"{SAVING_FOLDER}/DATA.json"
        if os.path.isfile(file):
            old_file = open(file, "r", encoding='utf-8')
            previous_data = json.load(old_file)
        else:
            previous_data = ['']
        data = previous_data + new_data
        with open(file, "w", encoding='utf-8') as datafile:
            json.dump(data, datafile, indent=2, ensure_ascii=False)
            print("Data progress saved.")
        CACHE.clear()
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
    """Service class for DataScraper"""

    def __init__(self, max_lists=100):
        self.max_lists = max_lists

    def download_links(self):
        if not self.is_done():
            self.ready_lists()
            print("lists downloaded.")
            lists_folder = f"{SAVING_FOLDER}/lists"
            listing_pages = [os.path.join(lists_folder, page) for page in os.listdir(
                lists_folder) if page.endswith(".html")]
            print("Downloading the links....")
            with concurrent.futures.ThreadPoolExecutor() as link_readers:
                link_readers.map(self.get_page_links, listing_pages)
            self.save_links()
        else:
            print("The links list file already exists.")

    def save_links(self):
        links_file = f"{SAVING_FOLDER}/all_links.txt"
        complete_list = list(np.concatenate(CACHE).flat)
        with open(links_file, 'w', encoding='utf-8') as output:
            for link in complete_list:
                output.write(f"{link}\n")
            output.close()
        CACHE.clear()
        print("The list of links is ready.\n")

    def is_done(self):
        return True if os.path.isfile(f"{SAVING_FOLDER}/all_links.txt") else False

    def get_page_links(self, html_file, max_links=57):
        page_text = open(html_file, 'r', encoding='utf-8').read()
        links = []
        bsp = bs4.BeautifulSoup(page_text, 'html.parser')
        for n in range(1, max_links):
            try:
                ad = str(bsp.select(CHILD_LINK.replace("+++", str(n)))[0])
                bsp2 = bs4.BeautifulSoup(ad, 'html.parser')
                for link in bsp2.find_all('a'):
                    address = link.get('href')
                    if address not in links:
                        links.append(address)
            except IndexError:
                continue

        if len(links) > 1:
            CACHE.append(links)
            print(f"{len(CACHE)} link pages processed...")
        else:
            raise Exception(
                "Error. No links found in the list page. Check the selectors.")

    def ready_lists(self):
        lists_folder = f'{SAVING_FOLDER}/lists'
        os.makedirs(lists_folder, exist_ok=True)
        print("downlading the lists of links...")
        self.__download_list_pages()

    def __download_list_pages(self):
        max_lists = self.max_lists
        lists_folder = rf'{SAVING_FOLDER}/lists'
        lists_downloaded = [os.path.join(lists_folder, file) for file in os.listdir(
            lists_folder) if file.endswith(".html")]
        if len(lists_downloaded) == 0:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(self.get_list_page, range(1, max_lists + 1))
        else:
            print(f"{len(lists_downloaded)} lists of links already downloaded")
        return

    def get_list_page(self, page_num):
        output_file = rf'{SAVING_FOLDER}/lists/list_page{page_num}.html'
        if os.path.isfile(output_file):
            return
        else:
            page_url = MAIN_URL.replace("+++", str(page_num))
            req = requests.get(page_url, headers=USER_AGENT)
            if req.status_code == 200:
                with open(output_file, 'w', encoding='utf-8') as output:
                    output.write(req.text)
                    output.close()
                    print("downloaded listing page ", page_num)
            else:
                raise Exception(
                    f"Error. Received status code {req.status_code} getting page {page_num}")
            return


if __name__ == "__main__":
    if not os.path.exists(LISTS_FOLDER):
        linksScraper = LinkScraper()
        linksScraper.download_links()
    datascraper = DataScraper()
    datascraper.run()

# with open(f"{SAVING_FOLDER}/to_read.json", 'r', encoding='utf-8') as f:
#     lista = json.load(f)
#     print(len(lista))
