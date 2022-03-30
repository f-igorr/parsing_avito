import csv

#headers = ['1','2']


res = [
    {'1': '11', '2': '22'},
    {'1': '33', '2': '44'}
]

headers = res[0].keys()

with open('eggs.csv', 'w', newline='') as csvfile:
    riter = csv.writer(csvfile, delimiter=';')
    riter.writerow(headers)
    for r in res:
        x = r.values()
        riter.writerow(x)