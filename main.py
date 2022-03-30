import requests
from bs4 import BeautifulSoup, SoupStrainer
import lxml
import re
import time
import random
import csv


HEADERS = {

    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
    'Accept': 'image/avif,image/webp,*/*'

}

URL_WO_PAGE = 'https://www.avito.ru/krasnodar/doma_dachi_kottedzhi/sdam/na_dlitelnyy_srok-ASgBAgICAkSUA9IQoAjIVQ?cd=1&f=ASgBAQECAkSUA9IQoAjIVQFA2gg01FnSWdZZAkXCExh7ImZyb20iOm51bGwsInRvIjoxNDY3NH3GmgwVeyJmcm9tIjowLCJ0byI6MjAwMDB9'

LOCATION_FILTER = '/krasnodar/'
PREFIX = 'https://www.avito.ru'

parser = 'lxml'
#parser = 'html5lib'
#parser = 'html.parser'
TIMEOUT = 5


def count_pages(url):
    ''' смотрим сколько страниц перебирать '''
    ''' 
    url: страница нач запроса
    '''
    print('Start count_pages')
    response = requests.get(url=url, headers=HEADERS, timeout= TIMEOUT)
    if response.status_code == 200:
        src = response.text
    else:
        return print('Bad status_code')
    #filter = SoupStrainer('div', class_ = re.compile('pagination-root')) #будем готовить суп только из 'div'
    soup = BeautifulSoup(src, parser) #, parse_only=filter)
    last_page = soup.find_all(attrs={f'data-marker': {re.compile('page')}})[-1].text.strip()

    print('last_page = ', last_page)

    return int(last_page) # номер послед страницы


def search_links_from_page(url):
    ''' собираем ссылки на обявл с конкретной страницы '''
    '''
    url: ссылка с номером страницы
    '''
    response = requests.get(url=url, headers=HEADERS, timeout= TIMEOUT)
    if response.status_code == 200:
        src = response.text
    else:
        return print('Bad status_code')
    #filter = SoupStrainer('a') #будем готовить суп только из ссылок
    soup = BeautifulSoup(src, parser) #, parse_only=filter)
    tags_links = soup.find_all('a', class_=re.compile('link-link'), href = re.compile(LOCATION_FILTER), attrs = {'data-marker': 'item-title'})
    links = []
    for tag in tags_links:
        link = tag.get('href')
        links.append(link)

    return links


def collect_all_links(last_pages):
    ''' перебор всех страниц '''
    '''
    last_pages: кол-во страниц
    '''
    all_links = []
    for p in range(1, last_pages + 1): # перебор страниц
        url = f'{URL_WO_PAGE}&p={str(p)}'
        try:
            print(f'Start search_links_from_page {p}')
            links_from_page = search_links_from_page(url)
            for x in links_from_page:
                if x in all_links:
                    pass
                else:
                    all_links.append(x)
        except:
            print('{p} ERR')
            break
        time.sleep(random.gauss(mu=10, sigma=2))

    return all_links


def collect_data(url):
    ''' собираем данные из одного объявления '''
    '''
    url: ссылка на конкретное объявление
    '''
    response = requests.get(url=url, headers=HEADERS, timeout= TIMEOUT)
    if response.status_code == 200:
        src = response.text
    else:
        return print('Bad status_code')
    res = {}
    soup = BeautifulSoup(src, parser) #, parse_only=filter)
    title       = soup.find('span', class_ = re.compile('title-info-title-text')).text.strip()
    price       = soup.find('span', class_ = re.compile('item-price'), attrs = {'itemprop': 'price'})['content']
    zalog       = soup.find('div', text = re.compile('залог')).text.strip().replace(u'\xa0', u' ')
    try:
        animals     = soup.find('span', text = re.compile('Можно с животными')).next_sibling.strip()
        with open(file='link_OK.html', mode='w') as file:
            file.write(response.text)
    except:
        with open(file='link_BAD.html', mode='w') as file:
            file.write(response.text)
    #animals     = soup.find('span', class_ = re.compile('item-params-label'), text = re.compile('Можно с животными')).next_sibling.strip()
    address     = soup.find('span', class_ = re.compile('item-address')).text.strip()
    description = soup.find('div', class_= re.compile('item-description-text'), itemprop='description').text.strip()
    seller      = soup.find(attrs = {'data-marker': 'seller-info/label'}).text.strip()
    date        = soup.find('div', class_= re.compile('title-info-metadata-item-redesign')).text.strip()
    
    res['title']       = title
    res['price']       = price
    res['zalog']       = zalog
    res['animals']     = animals
    res['condition']   = 'да' if re.findall(r'[Кк]ондиционер', description) else 'нет'
    res['seller']      = seller
    res['date']        = date
    res['address']     = address
    res['description'] = description
    res['url']         = url

    return res


def write_to_csv(result, filename='results.csv'):
    ''' запись в csv файл '''
    print('Start write_to_csv')
    headers = result[0].keys()
    with open(filename, mode='w') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(headers)
        for item in result:
            writer.writerow(item.values())

    return None


def main():
    
    last_pages = int(count_pages(URL_WO_PAGE))
    all_links = collect_all_links(last_pages)
    print('End collect_all_links')
    
    results = []
    count_links = 1
    for link in all_links:
        url = PREFIX + link
        print(f'Start collect_data {count_links} from {len(all_links)} url={url}')
        results.append(collect_data(url))
        time.sleep(random.gauss(mu=30.0, sigma=5.0))
        count_links += 1

    write_to_csv(results)

    return None #print(results)
        

if __name__ == '__main__':
    main()