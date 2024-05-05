# A simpler web scrapper that uses regex instead of
# beautifulsoup because the listing pages already contain the data we need
import csv
import json
import requests

import os
import re
import concurrent.futures


SAVING_FOLDER = os.path.join(os.path.join(
    os.environ['USERPROFILE']), 'Desktop')
USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}
entry_pattern = r'{"subject":".*?","title":".*?","price":".*?","listId":\d+,"lastBumpAgeSecs":"\d+","oldPrice":.*?,"professionalAd":.*?,"isFeatured":.*?,"listingCategoryId":"\d+","images":\[.*?\],"videoCount":\d+,"isChatEnabled":.*?,"fixedOnTop":.*?,"url":".*?","thumbnail":".*?","date":\d+,"imageCount":\d+,"location":".*?","locationDetails":{.*?},"category":".*?","searchCategoryLevelZero":\d+,"searchCategoryLevelOne":\d+,"properties":\[.*?\],"accountActivityStatus":{.*?},"position":\d+,"olxPay":{.*?},"olxPayBadgeEnabled":.*?,"olxDelivery":{.*?},"olxDeliveryBadgeEnabled":.*?,"installments":.*?,"vehicleReport":{.*?},"vehicleTags":\[.*?\],"vehiclePills":.*?,"isFavorited":.*?,"hasRealEstateHighlight":.*?,"trackingSpecificData":\[.*?\]}'
MAIN_URL = 'https://www.olx.com.br/imoveis/venda/estado-pb/paraiba/joao-pessoa?q=casa+jo%C3%A3o+pessoa&sd=4806&sd=4813&sd=4826&sd=4825&sd=4809&sd=4859&sd=4836&sd=4830&sd=4829&sd=4814&sd=4818&sd=4838&sd=4824&sd=4799&sd=4848&sd=4844&sd=4856&sd=4850&sd=4854&sd=4846&sd=4855&sd=4847&sd=4811&sd=4837&sd=4843&sd=4842&sd=4852&sd=4802&sd=4851&sd=4810&sd=4803&sd=4831&sd=4820&sd=4835&sd=4849&sd=4816&sd=4845&sd=4857&sd=4812&sd=4808&sd=4840&sd=4817&sd=4833&sd=4853&sd=4807&sd=4827&sd=4819&sd=4822&sd=4828&sd=4832&sd=4823&sd=4804&sd=4815&sd=4821&sd=4839&sd=4805&sd=4841&sd=4801&sd=4834&sd=4800&sd=4858&o=+++'
LISTS_FOLDER = f"{SAVING_FOLDER}/lists"



class OLXscrapper:
    def __init__(self, max_lists:200) -> None:
        self.buffer = []
        self.data = []
        self.max_lists = max_lists

    def run(self):
        self.get_listing_pages()
        self.read_pages_data()
        self.generate_csv()

    def get_listing_pages(self):
        lists_folder = f'{SAVING_FOLDER}/lists'
        os.makedirs(lists_folder, exist_ok=True)
        print("\ndownloading the lists of links...")
        lists_folder = rf'{SAVING_FOLDER}/lists'
        lists_downloaded = [os.path.join(lists_folder, file) for file in os.listdir(
            lists_folder) if file.endswith(".html")]

        if not len(lists_downloaded):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(self.__get_listing_page, range(1, self.max_lists + 1))
            return

        print(f"{len(lists_downloaded)} listing pages ready")
        return


    def __get_listing_page(self, page_num):
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


    def read_pages_data(self):
        lists_folder = f"{SAVING_FOLDER}/lists"
        listing_pages = [os.path.join(lists_folder, page) for page in os.listdir(
                lists_folder) if page.endswith(".html")]
        with concurrent.futures.ThreadPoolExecutor() as link_readers:
            link_readers.map(self.get_entries_from_page, listing_pages)

    def get_entries_from_page(self, html_page):
        page_text = open(html_page, 'r', encoding='utf-8').read()
        matches = re.findall(entry_pattern, page_text)
        results = []
        json_objects = []
        for match in matches:
            try:
                json_objects.append(json.loads(match))
            except json.JSONDecodeError:
                continue

        for obj in json_objects:
            properties_to_extract = ['iptu', 'size', 'rooms', 'bathrooms', 'garage_spaces']
            properties = obj.get("properties")
            entry = {
                "id": obj.get("listId"),
                "price": float(re.sub(r'[^\d]', '', obj.get("price", "0"))),
                "professionalAd": obj.get("professionalAd"),
                "description": obj.get('images', [{}])[0].get('originalAlt', ''),
                "isFeatured": obj.get("isFeatured"),
                "neighbourhood": obj.get("locationDetails",{}).get("neighbourhood"),
                "date": obj.get("date"),
                "category": obj.get("catetory"),
            }
            for prop in properties:
                if prop['name'] in properties_to_extract:
                    value_str = prop['value']
                    value_float = value_str
                    entry[prop['name']] = value_float

            results.append(entry)
        self.data = [*self.data, *results]


    def generate_csv(self):
        objects = self.data
        fieldnames = objects[0].keys() if objects else []

        with open(f"{SAVING_FOLDER}/jampa_housing.csv",  'w', newline='', encoding='utf-8',) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for obj in objects:
                writer.writerow(obj)


if __name__ == "__main__":
    scrapper = OLXscrapper(200)
    scrapper.run()