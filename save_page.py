import requests



HEADERS = {

    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
    'Accept': 'image/avif,image/webp,*/*'

}
URL_1 = 'https://www.avito.ru/krasnodar/doma_dachi_kottedzhi/dom_34_m_na_uchastke_3_sot._2363871707'
#URL_2 = 'https://www.avito.ru/krasnodar/doma_dachi_kottedzhi/dom_40_m_na_uchastke_1_sot._2276656851'

response = requests.get(url=URL_1, headers=HEADERS)
print(response.content)
with open(file='link_1.html', mode='w') as file:
   file.write(response) #.text)

#response = requests.get(url=URL_2, headers=HEADERS)
#with open(file='link_2.html', mode='w') as file:
#   file.write(response.text)