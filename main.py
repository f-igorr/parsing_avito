from ast import Raise
import requests
from bs4 import BeautifulSoup, SoupStrainer
import lxml
import re
import time
import random
import csv


# хедеры можно рандомно подставлять в запросы
HEADERS = [
    {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
    'Accept': 'image/avif,image/webp,*/*',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'
    },
    {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
    'accept': '*/*',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8'
    },
    {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
    'accept': 'image/avif,image/webp,*/*',
    'accept-language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'
    }
    ]

URL_WO_PAGE = 'https://www.avito.ru/krasnodar/doma_dachi_kottedzhi/sdam/na_dlitelnyy_srok-ASgBAgICAkSUA9IQoAjIVQ?cd=1&f=ASgBAQECAkSUA9IQoAjIVQFA2gg01FnSWdZZAkXCExh7ImZyb20iOm51bGwsInRvIjoxNDY3NH3GmgwZeyJmcm9tIjoxNTAwMCwidG8iOjE1MDAwfQ&s=1'

LOCATION_FILTER = '/krasnodar/'
PREFIX = 'https://www.avito.ru'

parser = 'lxml'
#parser = 'html5lib'
#parser = 'html.parser'
TIMEOUT = 5 # сколько ждем ответ 
#DICT_SLEEP_COUNT_PAGES = { 'mu': 2.0, 'sigma': 1.0 }
#TIME_SLEEP = { 'mu': 20.0, 'sigma': 5.0 } # [mu, sigma] для рандомной задержки запросов



def request_with_check_200(url, dict_sleep, text):
    ''' делаем запрос пока не получим статус 200 
    url: link
    time_sleep: {'mu': int, 'sigma': int} словарь 
    text: текст для печати инфо 
    '''
    status_200 = False
    count = 1 # счетчик попыток
    while not status_200: # пока status_200 = False посылаем запросы
        num_random_header = 0 #random.randint(0,len(HEADERS)-1) # рандомный индекс для списка хедеров
        rand_header = HEADERS[num_random_header]
        response = requests.get(url=url, headers=rand_header, timeout= TIMEOUT)
        if response.status_code == 200:
            print(f'{text}. попытка {count} OK')
            src = response.text
            status_200 = True
        else:
            print(f'{text}. попытка {count} BAD')
            time.sleep(random.gauss(mu=dict_sleep['mu'] * count, sigma=dict_sleep['sigma']))
            count += 1
        if count > 5:
            break
    
    return src, rand_header



def find_last_page(url, dict_sleep):
    ''' смотрим сколько страниц перебирать 
    url: страница нач запроса
    '''
    print('Start <find_last_page> ...')
    text = 'поиск номера последней страницы'
    src, rand_header = request_with_check_200(url, dict_sleep, text)
    filter = SoupStrainer('div') #, class_ = re.compile('pagination-root')) #будем готовить суп только из 'div'
    soup = BeautifulSoup(src, parser, parse_only=filter)
    last_page = soup.find_all(attrs={f'data-marker': {re.compile('page')}})[-1].text.strip()
    print('last_page = ', last_page)

    return int(last_page) # номер послед страницы


def collect_all_hrefs(url, dict_sleep, last_page):
    ''' перебор всех страниц 
    url: ссылка без номера страницы
    last_pages: номер последней страницы
    '''
    all_hrefs = []
    for page in range(1, last_page + 1): # перебор страниц
        url = f'{url}&p={str(page)}'
        print(f'Start <collect_all_hrefs> from page {page}...')
        text = f'загрузка страницы {page}'
        src, rand_header = request_with_check_200(url, dict_sleep, text)
        filter = SoupStrainer('a') #будем готовить суп только из ссылок
        soup = BeautifulSoup(src, parser, parse_only=filter)
        tags_links = soup.find_all(class_= re.compile('link-link'), href = re.compile(LOCATION_FILTER), attrs = {'data-marker': 'item-title'})
        for tag in tags_links:
            href = tag.get('href')
            if href in all_hrefs:
                pass
            else:
                all_hrefs.append(href)

    return all_hrefs


def collect_all_data(hrefs, dict_sleep):
    ''' собираем данные из одного объявления 
    hrefs: список ссылок на объявления
    '''
    all_data = []
    for i, href in enumerate(hrefs, start=1):
        print(f'collecting data url {i} / {len(hrefs)}')
        url = PREFIX + href
        text = f'загрузка объявления'
        src, rand_header = request_with_check_200(url, dict_sleep, text)
        dict_data = {}
        soup = BeautifulSoup(src, parser)

        #flag_not_found = True
        count = 1
        while count < 5: #flag_not_found == True:

            try:
                title       = soup.find('span', class_ = re.compile('title-info-title-text')).text.strip()
            except Exception:
                title = 'not found'

            try:        
                price       = soup.find('span', class_ = re.compile('item-price'), attrs = {'itemprop': 'price'})['content']
            except Exception:
                price = 'not found'

            try:
                zalog       = soup.find('div', text = re.compile('залог')).text.strip().replace(u'\xa0', u' ')
            except Exception:
                zalog = 'not found'    

            try:
                animals     = soup.find('span', text = re.compile('Можно с животными')).next_sibling.strip()
            except Exception:
                animals = 'not found'  
                with open(file='soup.txt', mode='w') as file:
                    file.write(soup.text)
                    raise

            try:    
                address     = soup.find('span', class_ = re.compile('item-address')).text.strip()
            except Exception:
                address = 'not found'   

            try:    
                description = soup.find('div', class_= re.compile('item-description'), itemprop='description').text.strip()
            except Exception:
                description = 'not found'    

            try:    
                seller      = soup.find(attrs = {'data-marker': 'seller-info/label'}).text.strip()
            except Exception:
                seller = 'not found'   

            try:    
                date        = soup.find('div', class_= re.compile('title-info-metadata-item-redesign')).text.strip()
            except Exception:
                date = 'not found'

            try:
                technics    = soup.find('span', text = re.compile('Техника:')).next_sibling.strip()
            except Exception:
                technics = 'not found'

            dict_data['title']       = title
            dict_data['price']       = price
            dict_data['zalog']       = zalog
            dict_data['animals']     = animals
            dict_data['condition']   = 'да' if re.findall(r'[Кк]ондиционер', description + technics) else 'нет'
            dict_data['seller']      = seller
            dict_data['date']        = date
            dict_data['address']     = address
            dict_data['technics']    = technics
            dict_data['description'] = description
            dict_data['url']         = url
            dict_data['rand_header'] = rand_header

            if 'not found' in dict_data.values():
                #flag_not_found = True
                print(f'not_found. trying again {count}...')
                time.sleep(random.gauss(mu=dict_sleep['mu'] * count, sigma=dict_sleep['sigma']))
                count += 1
            else:
                #flag_not_found = False
                break
                
        all_data.append(dict_data)
        
    return all_data


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
    
    dict_sleep = {'mu': 10.0, 'sigma': 1.0}
    last_page = find_last_page(URL_WO_PAGE, dict_sleep)

    dict_sleep = {'mu': 15.0, 'sigma': 2.0}
    while True:
        all_hrefs = collect_all_hrefs(URL_WO_PAGE, dict_sleep, last_page)
        all_hrefs_2 = collect_all_hrefs(URL_WO_PAGE, dict_sleep, last_page)
        if len(all_hrefs) == len(all_hrefs_2):
            break
    print('End collect_all_links')
    
    dict_sleep = {'mu': 30.0, 'sigma': 5.0}
    results = collect_all_data(all_hrefs, dict_sleep)

    write_to_csv(results)

    return None #print(results)
        

if __name__ == '__main__':
    main()