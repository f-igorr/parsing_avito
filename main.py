from ast import Raise
import string
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

URL_WO_PAGE = 'https://www.avito.ru/krasnodar/doma_dachi_kottedzhi/sdam/na_dlitelnyy_srok-ASgBAgICAkSUA9IQoAjIVQ?cd=1&f=ASgBAQECAkSUA9IQoAjIVQFA2gg01FnSWdZZAkXCExh7ImZyb20iOm51bGwsInRvIjoxNDY3Mn3GmgwVeyJmcm9tIjowLCJ0byI6MTYwMDB9&i=1'

LOCATION_FILTER = '/krasnodar/'
PREFIX = 'https://www.avito.ru'

parser = 'lxml'
#parser = 'html5lib'
#parser = 'html.parser'
TIMEOUT = 5 # сколько ждем ответ 
TIME_SLEEP = { 'mu': 5.0, 'sigma': 1.0 } # [mu, sigma] для рандомной задержки запросов



def request_with_check_200(url):
    ''' делаем запрос пока не получим статус 200 
    url: link
    '''
    time.sleep(random.gauss(mu=TIME_SLEEP['mu'], sigma=TIME_SLEEP['sigma']))
    status_200 = False
    count = 1 # счетчик попыток
    while not status_200: # пока status_200 = False посылаем запросы
        num_random_header = random.randint(0,len(HEADERS)-1) # рандомный индекс для списка хедеров
        rand_header = HEADERS[num_random_header]
        response = requests.get(url=url, headers=rand_header, timeout= TIMEOUT)
        if response.status_code == 200:
            src = response.text
            status_200 = True
        else:
            time.sleep(random.gauss(mu=TIME_SLEEP['mu'], sigma=TIME_SLEEP['sigma']))
            count += 1
        if count > 2:
            break
    
    return src, rand_header # rand_header записываю для инфы ошибок


def collect_all_hrefs(url_wo_page):
    ''' перебор страниц и поиск на них объявл с нужной локацией
    url_wo_page: ссылка без номера страницы
    '''
    all_hrefs = []
    page = 1
    while True:
        time.sleep(random.gauss(mu=2, sigma=0.5))
        url = f'{url_wo_page}&p={str(page)}'
        print(f'Start <collect_all_hrefs> from page {page}...')
        src, rand_header = request_with_check_200(url)
        soup = BeautifulSoup(src, parser) #, parse_only=filter)
        tags = soup.find_all('a', class_= re.compile('link-link'), href = re.compile(LOCATION_FILTER), attrs = {'data-marker': 'item-title'})
        if not tags:
            print(f'page {page} is empty')
            break
        else:
            for tag in tags:
                href = tag.get('href')
                if href in all_hrefs:
                    pass
                else:
                    all_hrefs.append(href)
            page += 1

    print('count hrefs:', len(all_hrefs))

    return all_hrefs


def write_to_dict(dict_data, key, val):
    '''  
    если в словаре нет такого ключа, то записываем значение;
    если в словаре значение 'not found', то обновляем;
    иначе ничего не делаем
    '''
    val_dict = dict_data.get(key, None)
    if val_dict is None:
        dict_data[key] = val
    elif  val_dict == 'not found':
        dict_data[key] = val
    else:
        pass

    return None #dict_data


def data_from_one_link(href):
    ''' собираем данные из одного объявления 
    href: ссылкa на объявлениe
    '''
    dict_data = {}
    url = PREFIX + href
    count = 1

    while count <= 3:

        time.sleep(random.gauss(mu=TIME_SLEEP['mu'] * count, sigma=TIME_SLEEP['sigma']))
        src, rand_header = request_with_check_200(url)
        soup = BeautifulSoup(src, parser)

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

        cond = 'да' if re.findall(r'[Кк]ондиционер|[Сс]плит', description + ' ' + technics) else 'нет'

        write_to_dict(dict_data, 'title', title)
        write_to_dict(dict_data, 'price', price)
        write_to_dict(dict_data, 'zalog', zalog)
        write_to_dict(dict_data, 'animals', animals)
        write_to_dict(dict_data, 'condition', cond)
        write_to_dict(dict_data, 'seller', seller)
        write_to_dict(dict_data, 'date', date)
        write_to_dict(dict_data, 'address', address)
        write_to_dict(dict_data, 'technics', technics)
        write_to_dict(dict_data, 'description', description)
        write_to_dict(dict_data, 'url', url)
        write_to_dict(dict_data, 'rand_header', rand_header)

        if 'not found' in dict_data.values():
            print(f'not_found. trying again {count}...')
            count += 1
        else:
            break
        
    return dict_data


def write_to_csv(result, filename):
    ''' запись в csv файл 
    result: list(dict) # лист словарей данных
    '''
    print('Start write_to_csv')
    headers = result[0].keys() # заголовки таблицы
    with open(filename, mode='w') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(headers)
        for item in result:
            writer.writerow(item.values())

    return None


def main():
    
    all_hrefs = collect_all_hrefs(URL_WO_PAGE)
    all_data = []
    len_hrefs = len(all_hrefs)
    for i, href in enumerate(all_hrefs, start=1):
        print(f'start collecting data href {i} / {len_hrefs}')
        all_data.append(data_from_one_link(href))

    write_to_csv(result=all_data, filename='result.csv')

    return None #print(results)
        

if __name__ == '__main__':
    main()