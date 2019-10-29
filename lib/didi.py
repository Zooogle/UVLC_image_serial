# _*_ coding=utf-8 _*_
import json
import csv



with open(r'C:\Users\alan\Desktop\pm2.5数据-陈飞\pm2.5数据-陈飞\20141201014648.txt', 'r', encoding = 'utf-8') as f:
    rows = json.load(f)

f = open(r'C:\Users\alan\Desktop\pm2.5数据-陈飞\pm2.5数据-陈飞\data1.csv', 'w')
csv_write = csv.writer(f)
csv_write.writerow(rows[0].keys())

for row in rows:
    csv_write.writerow(row.values())

f.close()

