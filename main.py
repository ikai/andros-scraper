from __future__ import print_function
import requests
from bs4 import BeautifulSoup
import json
from collections import defaultdict
import pprint

MENU_URL = 'https://www.androsrostilj.com/menus'

# Mobile version of the page
WIX_CONTENT_URL_TPL = 'https://static.wixstatic.com/sites/%s.z'

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

def andros_scraper():
    """ Returns a dictionary mapping days of the week to a list of food items. 
        Sample output:

            {u'Friday': [u'Seasonal Fresh Fruit (Vegan)',
                        u'Traditional Beef Chili (Gar)',
                        u'Iceberg Salad with Cherry Tomatoes, Cucumber and Grilled Onions with Bleu Cheese Dressing (D)(Tom)(Veget)',
                        u'Broccoli, Cauliflower and Carrots (Gar)(Vegan)',
                        u'Potato Wedges with Fresh Herbs (Gar)(Vegan)',
                        u'Three Bean and Quinoa Salad (Cil)(Tom)(Vegan)',
                        u'BBQ Vegan Tenders (G)(Gar)(Soy)(W)(Vegan)',
                        u'BBQ Chicken (Gar)',
                        u'BBQ Pork Ribs and Sausages (Gar)(P)',
                        u'Honey BBQ Sauce, Smokehouse BBQ Sauce, Tangy Carolina BBQ Sauce'],
            # .... etc

    """

    r = requests.get(MENU_URL)
    lines = r.text.splitlines()

    # JANK JANK JANK JANK JANK JANK JANK
    public_model_line = None
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('var publicModel = '):
            public_model_line = stripped_line
        
    # EVEN MORE JANK
    cleaned_line = public_model_line.strip('var publicModel = ').strip(';')
    j = json.loads(cleaned_line)
    page_list = j['pageList']
    
    page_json_filename = None
    for page in page_list['pages']:
        if page['title'] == 'MENUS':
            page_json_filename = page['pageJsonFileName']
    
    # Now we can use this to fetch the content
    wix_url = WIX_CONTENT_URL_TPL % page_json_filename

    content = requests.get(wix_url)
    content_parsed = content.json()

    document_data = content_parsed['data']['document_data']

    data_item_keys = [key for key in document_data.keys() if key.startswith('dataItem')]

    menu_body = None
    for k in data_item_keys:
        t = document_data[k]['text']
        if not 'Allergen Legend' in t:
            menu_body = t

    soup = BeautifulSoup(menu_body, 'html.parser')
    all_paragraphs = soup.find_all('p')

    menu_map = defaultdict(list)
    current_day = None
    for p in all_paragraphs:
        title_container = p.find(style='font-size:20px')
        if title_container is not None:            
            day = title_container.text.split('-')[0].strip()
            # Because the stuff is Unicode
            if str(day) in DAYS_OF_WEEK:
                current_day = day

        elif current_day is not None:
            text = p.text.strip()
            if len(text) > 0:

                # Handle the case that this contains multiple lines
                for line in text.splitlines():
                    menu_map[current_day].append(line)
    
    menu = dict(menu_map)
    return menu

def main():
    menu = andros_scraper()
    pprint.pprint(menu)

if __name__ == '__main__':
    main()
