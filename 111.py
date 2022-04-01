import re

str = 'привет вася петя маша Петя Вася'


res = re.findall(r'[Вв]ася|[Пп]етя', str)

print(res)

