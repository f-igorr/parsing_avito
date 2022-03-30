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
        num_random_header = random.randint(0,len(HEADERS)-1) # рандомный индекс для списка хедеров
        response = requests.get(url=url, headers=HEADERS[num_random_header], timeout= TIMEOUT)
        if response.status_code == 200:
            print(f'{text}. попытка {count} OK')
            src = response.text
            status_200 = True
        else:
            print(f'{text}. попытка {count} BAD')
            time.sleep(random.gauss(mu=dict_sleep['mu'] * count, sigma=dict_sleep['sigma']))
            count += 1
    
    return src



def find_last_page(url):
    ''' смотрим сколько страниц перебирать 
    url: страница нач запроса
    '''
    print('Start <find_last_page> ...')
    dict_sleep = {'mu': 2.0, 'sigma': 1.0}
    text = 'поиск номера последней страницы'
    src = request_with_check_200(url, dict_sleep, text)
    filter = SoupStrainer('div') #, class_ = re.compile('pagination-root')) #будем готовить суп только из 'div'
    soup = BeautifulSoup(src, parser, parse_only=filter)
    last_page = soup.find_all(attrs={f'data-marker': {re.compile('page')}})[-1].text.strip()
    print('last_page = ', last_page)

    return int(last_page) # номер послед страницы


#def search_links_from_page(url):
#    ''' собираем ссылки на обявл с конкретной страницы 
#    url: ссылка с номером страницы
#    '''
#    print('Start search_links_from_page...')
#    dict_sleep = {'mu': 2.0, 'sigma': 1.0}
#    text = 'загрузка страницы с объявлениями'
#    src = request_with_check_200(url, dict_sleep, text)
#
#    #filter = SoupStrainer('a') #будем готовить суп только из ссылок
#    soup = BeautifulSoup(src, parser) #, parse_only=filter)
#    tags_links = soup.find_all('a', class_=re.compile('link-link'), href = re.compile(LOCATION_FILTER), attrs = {'data-marker': 'item-title'})
#    links = []
#    for tag in tags_links:
#        link = tag.get('href')
#        links.append(link)
#
#    return links


def collect_all_hrefs(url, last_page):
    ''' перебор всех страниц 
    url: ссылка без номера страницы
    last_pages: номер последней страницы
    '''
    all_hrefs = []
    dict_sleep = {'mu': 2.0, 'sigma': 1.0}
    for page in range(1, last_page + 1): # перебор страниц
        url = f'{url}&p={str(page)}'
        print(f'Start <collect_all_hrefs> from page {page}...')
        text = f'загрузка страницы {page}'
        src = request_with_check_200(url, dict_sleep, text)
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


def collect_all_data(hrefs):
    ''' собираем данные из одного объявления 
    hrefs: список ссылок на объявления
    '''
    all_data = []
    dict_sleep = {'mu': 2.0, 'sigma': 1.0}
    for i, href in enumerate(hrefs):
        print(f'collecting data url {i} / {len(hrefs)}')
        url = PREFIX + href
        text = f'загрузка объявления'
        src = request_with_check_200(url, dict_sleep, text)
        dict_data = {}
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
            description = soup.find('div', class_= re.compile('item-description-text'), itemprop='description').text.strip()
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
            technics = soup.find('li', class_= re.compile('params-paramsList')).text.strip()
        except Exception:
            technics = 'not found'





def collect_data_2(url):
    ''' собираем данные из одного объявления 
    url: ссылка на конкретное объявление
    '''
    num_random_header = random.randint(0,len(HEADERS)-1) # рандомный индекс для списка хедеров
    response = requests.get(url=url, headers=HEADERS[num_random_header], timeout= TIMEOUT)
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
    
    last_page = find_last_page(URL_WO_PAGE)

    while True:
        all_hrefs = collect_all_hrefs(URL_WO_PAGE, last_page)
        all_hrefs_2 = collect_all_hrefs(URL_WO_PAGE, last_page)
        if len(all_hrefs) == len(all_hrefs_2):
            break
    print('End collect_all_links')
    


    results = []
    count_links = 1
    for link in all_links:
        url = PREFIX + link
        print(f'Start collect_data {count_links} from {len(all_links)} url={url} ...')
        results.append(collect_data(url))
        time.sleep(random.gauss(mu=TIME_SLEEP['mu'], sigma=TIME_SLEEP['sigma']))
        count_links += 1

    write_to_csv(results)

    return None #print(results)
        

if __name__ == '__main__':
    main()