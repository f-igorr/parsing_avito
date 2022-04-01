import requests
from bs4 import BeautifulSoup
import re



HEADERS = {

    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
    'Accept': 'image/avif,image/webp,*/*'

}
URL_1 = 'https://www.avito.ru/krasnodar/doma_dachi_kottedzhi/dom_60_m_na_uchastke_4_sot._2352410171'
#URL_2 = 'https://www.avito.ru/krasnodar/doma_dachi_kottedzhi/dom_40_m_na_uchastke_1_sot._2276656851'

response = requests.get(url=URL_1, headers=HEADERS)
with open(file='link_1.html', mode='w') as file:
   file.write(response.text)

#response = requests.get(url=URL_2, headers=HEADERS)
#with open(file='link_2.html', mode='w') as file:
#   file.write(response.text)

with open(file='link_1.html') as file:
    src = file.read()

soup = BeautifulSoup(src, 'lxml')
try:
    #technics    = soup.find_all('li', class_= 'item-params-list-item').find('span', text = re.compile('Техника:')).text.strip()
    technics    = soup.find('span', text = re.compile('Техника:')).next_sibling.strip()
except Exception:
    technics = 'not found'

try:    
    description = soup.find('div', class_= re.compile('item-description'), itemprop='description').text.strip()
except Exception:
    description = 'not found'

try:
    animals     = soup.find('span', text = re.compile('Можно с животными')).next_sibling.strip()
except Exception:
    animals = 'not found'  

print('technics = ', technics)
print('description = ', description)
print('animals = ', animals)