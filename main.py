#codes were run on google's colab!


# 1.用指令來下載ttf檔(台北黑體之字型檔)
!wget -O taipei_sans_tc_beta.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
  
  
# 2.程式主體
#print('Hello')
"""
名稱: 台股分析__爬蟲
功能: 輸入股票代碼，即可產出
  1.資產負債與股東權益堆疊直條圖
  2.現金流量圖堆疊圖
  3.競爭力折線圖
  4.報酬率折線圖
  5.相關資訊的表格



url分析:
第一店(2706)
資產負債表: https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=BS_M_QUAR&STOCK_ID=2706
損益表: https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=IS_M_QUAR_ACC&STOCK_ID=2706
現金流量表: https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=CF_M_QUAR_ACC&STOCK_ID=2706

台積電(2330)
資產負債表: https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=BS_M_QUAR&STOCK_ID=2330
損益表: https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=IS_M_QUAR_ACC&STOCK_ID=2330
現金流量表: https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=CF_M_QUAR_ACC&STOCK_ID=2330


觀察: 
  1.各個表的url中差異只在最後的股票代碼
  2.損益表與現金流量表中，「累計」與「單季」不影響url -> 可以透過url參數來對應「累計」、「單季」..等等
    --單季: CF_M_QUAR
    --累季: CF_M_QUAR_ACC
    --年度: CF_M_YEAR

    
  =========================以上的方式得到的是最新的數據，若要調整起始時間，要參考下方============================
  
  3.調整起始季時間，是透過XHR拿到新的table，再更新到網頁上 -> 如何取得XHR? 
  以現金流量表為例:
  選2022Q3:
  https://goodinfo.tw/tw/StockFinDetail.asp?STEP=DATA&STOCK_ID=2330&RPT_CAT=CF_M_QUAR&QRY_TIME=20223
  選2022Q2
  https://goodinfo.tw/tw/StockFinDetail.asp?STEP=DATA&STOCK_ID=2330&RPT_CAT=CF_M_QUAR&QRY_TIME=20222
  選2020Q3
  https://goodinfo.tw/tw/StockFinDetail.asp?STEP=DATA&STOCK_ID=2330&RPT_CAT=CF_M_QUAR&QRY_TIME=20203

  回傳的是資料更新後的table! -> 從裡面撈數據即可
  

"""

#測試1: 取得台積電(2330)最新「資產負債表」數據
import requests
from bs4 import BeautifulSoup as BS
import re
import matplotlib.pyplot as plt
#from matplotlib.font_manager import FontProperties
import pandas as pd
import matplotlib as mpl
import matplotlib.font_manager
from matplotlib.font_manager import fontManager
from matplotlib.ticker import MaxNLocator
from matplotlib.pyplot import MultipleLocator
import numpy as np

#test
"""
a = sorted([f.name for f in mpl.font_manager.fontManager.ttflist])
#mpl.use('Agg')
for i in a:
  print(i)
"""
#==================================== DEFINITION ===============================

#取得股票代碼，若輸入錯誤(title會有9999年) -> 要重新請使用者輸入一次
print('財報資料取自Goodinfo!台灣股市資訊網')
stock_code = input('請輸入股票代碼: ')
#stock_code = str(2330)  #測試用，到時候要註記掉

#資產負債表url
url_balance_sheet = 'https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=BS_M_QUAR&STOCK_ID=' + stock_code

#損益表url
url_income_statement = 'https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=IS_M_QUAR&STOCK_ID=' + stock_code

#現金流量表
url_cash_flow = 'https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=CF_M_QUAR&STOCK_ID=' + stock_code

#統整url
urls = [url_balance_sheet, url_income_statement, url_cash_flow]

#財務報表統整
total_data = {'季度': []}

#公司名稱
company_name = ''

#設定作圖的中文字字型
#!wget -O taipei_sans_tc_beta.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
#!mv taipei_sans_tc_beta.ttf /usr/local/lib/python3.7/dist-packages/matplotlib//mpl-data/fonts/ttf
fontManager.addfont('taipei_sans_tc_beta.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')

#myfont = FontProperties(fname=r'/usr/local/lib/python3.7/dist-packages/matplotlib/mpl-data/fonts/ttf/taipei_sans_tc_beta.ttf')
#plt.rcParams['font.sans-serif'] = ['Taipei Sans TC Beta']

#列出所需欄位的資料，之後一次取得 -> (製造業與金融業的財報格式不同!!)
want_column = [
  '資產總額', '存貨', '負債總額', '股東權益總額', '每股淨值(元)', '營業收入', '營業成本', '營業毛利', '營業費用', '營業支出',
  '營業利益', '業外損益合計', '稅後淨利', '每股稅後盈餘(元)', '營業活動之淨現金流入(出)', '投資活動之淨現金流入(出)',
  '融資活動之淨現金流入(出)'
]

want_column_test = [
  '資產總額',
  '存貨',
  '負債總額',
  '股東權益總額',
  '每股淨值(元)',
  '營業收入',
  '營業成本',
  '營業毛利',
  '營業費用',
]

#==================================== 函數定義 ===================================


#函數: 將有逗號的文字轉成數字(去除掉逗號)
def text_to_number(text):
  clean_text = text.replace(',', '')
  actual_number = float(clean_text)
  return actual_number


#將數據視覺化，並存檔
def showResult(data, want_columns, company_name):
  print('呼叫成功')

  #test
  """
  x = list(range(-8, 8))
  y = [i**3 + 2 * i**2 + i for i in x]
  plt.plot(x, y)
  plt.title('First figure中文', {'fontsize': 15})
  plt.show()
  """

  #圖一: 資產負債與股東權益堆疊圖
  fig1 = plt.subplot(111)
  fig1.yaxis.set_major_locator(MaxNLocator(10))
  x = data['季度']
  x.reverse()
  liabilities = data['負債總額']
  liabilities.reverse()
  equities = data['股東權益總額']
  equities.reverse()

  plt.bar(x,liabilities,color='blue',label='總負債', width=0.6, zorder=3)
  plt.bar(x,equities,color='green',label='股東權益', width=0.6, bottom=liabilities, zorder=3)
  plt.title('資產負債與股東權益(' + company_name + ')', fontsize=18)
  plt.xticks(rotation=45)
  plt.ylabel('億元')
  plt.legend(bbox_to_anchor=(1,0.7), loc='upper left')
  plt.grid(axis='y')
  plt.show()
  #plt.savefig('圖片1')




  #圖二: 現金流量堆疊圖
  fig2 = plt.subplot(111)
  fig2.yaxis.set_major_locator(MaxNLocator(10)) #設定y軸刻度數量
  operating = data['營業活動之淨現金流入(出)']
  operating.reverse()
  investing = data['投資活動之淨現金流入(出)']
  investing.reverse()
  financing = data['融資活動之淨現金流入(出)']
  financing.reverse()

  plt.bar(x,operating,color='blue',label='營業現金', width=0.6, zorder=3)

  #根據金流的正負值決定是往上堆疊或是往下堆疊
  #參考: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.bar.html
  baseline = []
  #print(type(investing))
  for idx in range(7):
    if(investing[idx] < 0):
      if(operating[idx] < 0):
        baseline.append(operating[idx]) 
      else:
        baseline.append(0) 
    else:
      if(operating[idx] < 0):
        baseline.append(0) 
      else:
        baseline.append(operating[idx]) 


  plt.bar(x,investing,color='green',label='投資現金', width=0.6, zorder=3, bottom=baseline)

  baseline2 = []
  for idx in range(7):
    if(investing[idx]*financing[idx] >= 0):
      baseline2.append(investing[idx])
      #print('first')
    else:
      if(operating[idx]*investing[idx] >= 0):
        baseline2.append(0)
        #print('second')
      else:
        baseline2.append(operating[idx])
        #print('third')
        #print(operating[idx]*investing[idx])

  plt.bar(x,financing,color='gray',label='融資現金', width=0.6, zorder=3, bottom=baseline2)

  plt.title('現金流量(' + company_name + ')', fontsize=18)
  plt.xticks(rotation=45)
  plt.ylabel('億元')
  plt.legend(bbox_to_anchor=(1,0.7), loc='upper left')
  plt.grid(axis='y')
  plt.show()



  #圖三: 競爭力折線圖 
  fig3 = plt.subplot()
  
  #fig3.yaxis.set_major_locator(MultipleLocator(10)) #設定y軸刻度間距
  fig3.yaxis.set_major_locator(MaxNLocator(10)) #-> 無法多種設定都用上

  
  
  
  revenue = data['營業收入']
  revenue.reverse()
  revenue = np.array(revenue)

  #針對金融業，會有找不到「營業利益」的問題 -> 要自己算
  operating_income = []
  if('營業利益' in data.keys()):
    operating_income = data['營業利益']
    operating_income.reverse()
    print(len(operating_income))
  elif((not ('營業利益' in data.keys())) and ('營業支出' in data.keys())):
    operating_expenditure = data['營業支出']
    operating_expenditure.reverse()
    operating_expenditure = np.array(operating_expenditure)
    operating_income = revenue + operating_expenditure
    data['營業利益'] = list(operating_income)
    #print(len(operating_income))
  else:
    print('Something wrong?')

  #print('營業支出:'+data['營業支出'])
  #print('營業利益:'+data['營業利益'])
  
  operating_income = np.array(operating_income)
  operating_margin = operating_income / revenue * 100
  lns1 = fig3.plot(x,operating_margin, color='orange', marker='o', label='營業利益率')

  
  gross_profit=[]
  if('營業毛利' in data.keys()):
    gross_profit = data['營業毛利']
    gross_profit.reverse()
    gross_profit = np.array(gross_profit)
    
    
  else:
    gross_profit = revenue
  

  gross_profit_margin = gross_profit / revenue * 100
  lns2 = fig3.plot(x,gross_profit_margin,color='gray', marker='v',label='毛利率')
  net_profit = data['稅後淨利']
  net_profit.reverse()
  net_profit = np.array(net_profit)
  net_profit_margin = net_profit / revenue * 100
  lns3 = fig3.plot(x,net_profit_margin,color='gold', marker='^',label='稅後純益率')


  earn_per_share = data['每股稅後盈餘(元)']
  earn_per_share.reverse()
  lns4 = fig3.plot(x,earn_per_share,color='blue', marker='*',label='EPS每股盈餘')

  fig3_1 = fig3.twinx()
  lns5 = fig3_1.plot(x,revenue,color='green', marker='D',label='營收')


  #plt.ylim(bottom=0)  #上限該如何設定，維持10為間距(?)，且包含整體的最大值? -> OK
  #設定上下臨界值
  fig3_max_max = max(max(operating_margin),max(gross_profit_margin),max(net_profit_margin),max(earn_per_share))
  fig3_min_min = min(min(operating_margin),min(gross_profit_margin),min(net_profit_margin),min(earn_per_share))
  fig3_interval = (fig3_max_max - fig3_min_min) / 10
  fig3.set_ylim([fig3_min_min - fig3_interval, fig3_max_max + fig3_interval]) #bug! 要考慮有負數的情況

  fig3_1_interval = max(revenue)/((int(max(gross_profit_margin))+10)/10)
  fig3_1.set_ylim(bottom=0,top=max(revenue)+fig3_1_interval)  #bug! 要考慮有負數的情況


  plt.title('競爭力(' + company_name + ')', fontsize=18)
  fig3.set_ylabel('%')
  fig3_1.set_ylabel('億元')
  plt.grid(axis='y')
  plt.xticks(rotation=45)

  #將雙y軸的label合併顯示
  lns = lns1 + lns2 + lns3 + lns4 + lns5
  labels = [l.get_label() for l in lns]
  plt.legend(lns, labels, bbox_to_anchor=(1.15,0.7), loc='upper left')
  plt.show()



  #圖4: 報酬率折線圖
  fig4 = plt.subplot(111)
  fig4.yaxis.set_major_locator(MaxNLocator(7))
  equities = np.array(equities)
  return_on_equity = net_profit / equities * 100
  fig4.plot(x,return_on_equity,color='blue', marker='o',label='ROE股東權益報酬率')
  total_assets = data['資產總額']
  total_assets.reverse()
  total_assets = np.array(total_assets)
  return_on_assets = net_profit / total_assets * 100
  fig4.plot(x,return_on_assets,color='orange', marker='o',label='ROA資產報酬率')


  fig4_max_max = max(max(return_on_equity),max(return_on_assets))
  fig4_min_min = min(min(return_on_equity),min(return_on_assets))
  fig4_interval = (fig4_max_max - fig4_min_min) / 7
  fig4.set_ylim([fig4_min_min - fig4_interval, fig4_max_max + fig4_interval])
  fig4.legend(bbox_to_anchor=(1,0.7), loc='upper left')
  fig4.grid(axis='y')
  plt.title('報酬率(' + company_name + ')', fontsize=18)
  fig4.set_ylabel('%')
  plt.show()


  #在畫面上呈現財報(用print的方式)
  #轉換成表格的形式
  #經過上面的操作，部分的list已經被轉換順序了 -> 先把剩下未轉換順序的都轉好，再來增加新內容，最後輸出
  if('存貨' in data.keys()):
    inventory=data['存貨']
    inventory.reverse()
  
  new_worth=data['每股淨值(元)']
  new_worth.reverse()
  if('營業成本' in data.keys()):
    operating_cost=data['營業成本']
    operating_cost.reverse()
  
  
  operating_expenses=data['營業費用']
  operating_expenses.reverse()

  if('業外損益合計' in data.keys()):
    non_industry_profit_and_cost=data['業外損益合計']
    non_industry_profit_and_cost.reverse()
  

  #增加各個比率
  data['營業利益率']=list(operating_margin)
  data['毛利率']=list(gross_profit_margin)
  data['稅後純益率']=list(net_profit_margin)

  #以表格方式呈現在console
  print()
  print(company_name, '財務報表統整(單位為「億元」或「%」):')
  for title, values in data.items():
    print('{}'.format(title), end=': ')
    for val in values:
      #mytype=str(type(val))
      #print('{0:<30}'.format(mytype), end=' ')
      if(type(val) == np.float64):
        print('{:.2f}'.format(val), end=', ')
      else:
        print('{}'.format(val), end=', ')
    print()
  #print(data)

  """
  answer = input('\n是否要輸出成excel檔?(Y/N):')
  if(answer == 'Y' or answer == 'y'):
    outputFile()
    print('輸出完成!')
  else:
    print('程式結束')
  """



def outputFile():
  print('excel檔輸出!')





  """
  #畫表格 -> 不需要了
  
  ax = plt.subplot(111)
  #dataa = [[1, 2, 3], [4, 45, 6], [7, 8, 9]]
  #column_labels = ['Column 1', 'Column 2', 'Column 3']
  
  #print(data['季度'])
  col_names = list(data)  #從dict中將key值當作column name

  
  #print(data['我沒有我沒有?'])
  for idx, q in enumerate(data['季度']):
    temp_list = [q]

    for val in want_columns:
      temp_list.append(data[val][idx])

    financial_statement_table.insert(0, temp_list)

  #print(col_names)
  #將table以圖的方式顯示，不切實際，而且內容會變成"--"
  #print(financial_statement_table)
  print('輸出完成')

  
  ax.axis('tight')
  ax.axis('off')
  ax.table(cellText=financial_statement_table,
           colLabels=col_names,
           loc="center")
  #plt.show()
  #plt.savefig('test.png')
  """

  #輸出成excel檔(或csv)
  """
  writer = pd.ExcelWriter("output_file.xls")  #表格資料內容
  excel_header = want_columns  #表格欄位名稱
  df = pd.DataFrame(financial_statement_table)
  df.to_excel(writer, sheet_name="工作簿_分頁1", header=excel_header, index=False)
  writer.close()
  """
  
  


#user-agent定義，防止爬蟲被擋
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
headers = {'user-agent': user_agent}

#測試用
#台積電
dataa = {
  '季度': ['2022Q3', '2022Q2', '2022Q1', '2021Q4', '2021Q3', '2021Q2', '2021Q1'],
  '資產總額': [46433.0, 43459.0, 39927.0, 37255.0, 33323.0, 30928.0, 29191.0],
  '存貨': [2183.0, 2174.0, 2001.0, 1931.0, 1822.0, 1704.0, 1546.0],
  '負債總額': [18910.0, 18355.0, 16712.0, 15548.0, 12540.0, 10988.0, 9781.0],
  '股東權益總額': [27523.0, 25105.0, 23215.0, 21707.0, 20783.0, 19940.0, 19410.0],
  '每股淨值(元)': [105.59, 96.27, 89.26, 83.62, 80.06, 76.81, 74.77],
  '營業收入': [6131.0, 5341.0, 4911.0, 4382.0, 4147.0, 3721.0, 3624.0],
  '營業成本': [2426.0, 2187.0, 2179.0, 2074.0, 2019.0, 1859.0, 1726.0],
  '營業毛利': [3705.0, 3155.0, 2732.0, 2308.0, 2127.0, 1862.0, 1898.0],
  '營業費用': [601.9, 533.7, 486.1, 478.8, 416.5, 405.8, 391.1],
  '營業利益': [3103.0, 2621.0, 2238.0, 1828.0, 1710.0, 1457.0, 1505.0],
  '業外損益合計': [63.67, 38.75, 30.42, 20.47, 28.48, 37.24, 45.26],
  '稅後淨利': [2809.0, 2370.0, 2027.0, 1662.0, 1563.0, 1344.0, 1397.0],
  '每股稅後盈餘(元)': [10.83, 9.14, 7.82, 6.41, 6.02, 5.18, 5.39],
  '營業活動之淨現金流入(出)': [4127.0, 3388.0, 3722.0, 3782.0, 3187.0, 1874.0, 2278.0],
  '投資活動之淨現金流入(出)':
  [-2844.0, -2759.0, -2881.0, -2453.0, -1770.0, -1698.0, -2443.0],
  '融資活動之淨現金流入(出)': [-1304.0, 190.8, -190.9, 822.8, -353.2, 750.3, 146.2]
}

#玉山金
dataa2 = {
  '季度': ['2022Q3', '2022Q2', '2022Q1', '2021Q4', '2021Q3', '2021Q2', '2021Q1'], 
  '資產總額': [34917.0, 33433.0, 32925.0, 32309.0, 30523.0, 30007.0, 29283.0], 
  '負債總額': [33061.0, 31596.0, 30961.0, 30365.0, 28627.0, 28079.0, 27408.0], 
  '股東權益總額': [1856.0, 1837.0, 1965.0, 1944.0, 1897.0, 1927.0, 1875.0], 
  '每股淨值(元)': [12.99, 13.75, 14.7, 14.54, 14.19, 15.32, 14.91], 
  '營業收入': [143.5, 121.3, 135.5, 146.7, 151.9, 143.4, 137.0], 
  '營業費用': [81.31, 77.0, 78.67, 82.37, 79.89, 77.66, 78.17], 
  '營業支出': [-87.46, -82.32, -82.12, -92.87, -87.59, -84.33, -74.59], 
  '稅後淨利': [45.63, 27.59, 43.25, 46.74, 56.38, 50.43, 52.05], 
  '每股稅後盈餘(元)': [0.32, 0.19, 0.32, 0.35, 0.42, 0.4, 0.41], 
  '營業活動之淨現金流入(出)': [517.3, 104.4, 55.19, 280.0, -17.45, 163.6, -36.51], 
  '投資活動之淨現金流入(出)': [-16.08, -36.17, -42.24, -18.34, 22.38, -1.51, -48.63], 
  '融資活動之淨現金流入(出)': [62.84, -108.4, 53.66, 15.3, -76.74, 17.09, 10.49]
}

#精英
dataa3 = {
  '季度': ['2022Q3', '2022Q2', '2022Q1', '2021Q4', '2021Q3', '2021Q2', '2021Q1'], 
  '資產總額': [240.3, 249.7, 234.7, 241.3, 246.6, 236.2, 234.7], 
  '存貨': [30.38, 38.66, 45.2, 43.19, 52.83, 47.78, 41.85], 
  '負債總額': [124.0, 138.3, 126.6, 136.2, 142.8, 133.0, 126.7], 
  '股東權益總額': [116.3, 111.4, 108.0, 105.1, 103.7, 103.1, 108.0], 
  '每股淨值(元)': [20.85, 19.92, 19.32, 18.73, 18.48, 18.38, 19.24], 
  '營業收入': [75.55, 107.8, 74.61, 95.9, 83.96, 74.37, 65.15], 
  '營業成本': [66.48, 97.66, 68.68, 87.94, 76.07, 68.33, 60.42], 
  '營業毛利': [9.07, 10.17, 5.92, 7.96, 7.9, 6.04, 4.72], 
  '營業費用': [8.66, 7.69, 5.95, 7.39, 7.26, 7.3, 7.27], 
  '營業利益': [0.41, 2.48, -0.032, 0.57, 0.64, -1.27, -2.55], 
  '業外損益合計': [5.3, 1.85, 2.34, 0.7, 1.01, 2.19, 0.39], 
  '稅後淨利': [4.1, 3.44, 1.77, 1.14, 0.83, 0.97, -2.22], 
  '每股稅後盈餘(元)': [0.74, 0.61, 0.32, 0.21, 0.16, 0.17, -0.4], 
  '營業活動之淨現金流入(出)': [22.19, 2.58, 16.94, -3.19, 0.38, -13.26, -3.93], 
  '投資活動之淨現金流入(出)': [-2.83, -5.7, -4.88, 4.47, 0.2, 3.39, 4.74], 
  '融資活動之淨現金流入(出)': [-9.19, 4.59, -3.33, -7.74, -0.53, 3.25, -4.74]
}

#羅麗芬
dataa4 = {
  '季度': ['2022Q3', '2022Q2', '2022Q1', '2021Q4', '2021Q3', '2021Q2', '2021Q1'], 
  '資產總額': [22.53, 22.13, 21.13, 20.07, 20.22, 20.21, 20.53], 
  '存貨': [0.67, 0.77, 0.81, 0.72, 0.77, 0.98, 1.16], 
  '負債總額': [5.97, 5.75, 4.37, 4.02, 4.55, 3.58, 4.06], 
  '股東權益總額': [16.55, 16.38, 16.75, 16.05, 15.68, 16.63, 16.48], 
  '每股淨值(元)': [34.69, 34.31, 35.25, 33.76, 32.97, 34.97, 34.65], 
  '營業收入': [2.16, 2.76, 1.84, 2.55, 1.96, 2.85, 1.81], 
  '營業成本': [0.94, 1.09, 0.67, 0.98, 0.96, 1.17, 0.72], 
  '營業毛利': [1.22, 1.68, 1.17, 1.57, 1.01, 1.68, 1.08], 
  '營業費用': [1.2, 1.24, 1.08, 1.43, 1.09, 1.27, 1.02], 
  '營業利益': [0.026, 0.44, 0.088, 0.14, -0.08, 0.41, 0.06], 
  '業外損益合計': [0.16, 0.13, 0.1, 0.14, 0.075, 0.074, 0.11], 
  '稅後淨利': [0.11, 0.5, 0.16, 0.25, 0.013, 0.29, 0.15], 
  '每股稅後盈餘(元)': [0.23, 1.06, 0.34, 0.53, 0.03, 0.62, 0.31], 
  '營業活動之淨現金流入(出)': [1.12, -2.19, -0.13, 0.72, -1.07, 3.73, -1.13], 
  '投資活動之淨現金流入(出)': [-0.86, -0.24, 1.32, -0.24, 0.57, -2.77, -0.15], 
  '融資活動之淨現金流入(出)': [-0.077, 0.17, 0.99, -0.97, 0.24, 0.018, -0.03]
}

#矽統
dataa5 = {
  '季度': ['2022Q3', '2022Q2', '2022Q1', '2021Q4', '2021Q3', '2021Q2', '2021Q1'], 
  '資產總額': [139.0, 156.7, 197.5, 233.8, 235.1, 195.2, 186.3], 
  '存貨': [1.3, 1.31, 1.3, 1.19, 0.95, 0.75, 0.74], 
  '負債總額': [1.11, 6.85, 0.97, 1.15, 6.14, 0.87, 0.78], 
  '股東權益總額': [137.9, 149.8, 196.5, 232.6, 228.9, 194.3, 185.5], 
  '每股淨值(元)': [18.39, 21.96, 28.81, 34.1, 33.55, 30.79, 29.39], 
  '營業收入': [0.35, 0.6, 0.43, 0.68, 0.73, 0.6, 0.51], 
  '營業成本': [0.39, 0.58, 0.32, 0.45, 0.45, 0.45, 0.33], 
  '營業毛利': [-0.037, 0.025, 0.11, 0.24, 0.28, 0.14, 0.18], 
  '營業費用': [1.1, 1.51, 1.01, 1.15, 1.21, 1.06, 0.98], 
  '營業利益': [-1.13, -1.49, -0.91, -0.92, -0.93, -0.91, -0.8], 
  '業外損益合計': [0.13, 8.61, 1.03, 0.11, 4.6, 0.014, 0.78], 
  '稅後淨利': [-0.93, 6.63, 0.17, -0.72, 4.2, -1.5, 0.002], 
  '每股稅後盈餘(元)': [-0.12, 0.97, 0.03, -0.11, 0.62, -0.24, 0.0], 
  '營業活動之淨現金流入(出)': [7.58, -10.19, -1.18, -0.86, -0.64, -0.87, -1.19], 
  '投資活動之淨現金流入(出)': [-0.084, 8.56, 0.99, -0.057, 4.22, 1.01, 1.51], 
  '融資活動之淨現金流入(出)': [-5.47, -0.024, -0.023, -4.99, 0.27, -0.006, -0.024]
}

#showResult(dataa5, want_column, 'company_name')

#============================== MAIN FUNCTION ==============================

for idx, url in enumerate(urls):
  res = requests.get(url, headers=headers)
  res.encoding = 'utf-8'
  #print(res.text)

  soup = BS(res.text, 'html.parser')
  #print(soup)

  if not (re.search('\w*9999\w*', soup.find('title').text)):
    #print('對惹')

    if (company_name == ''):
      temp_company_name = re.search('\(\d{4}\)(\w*)',
                                    soup.find('title').text).group(0)
      company_name = temp_company_name[6:len(temp_company_name)]
      #print(soup.find('title').text)
      print(company_name)

    table = soup.find('table', id='tblFinDetail')
    #print(table)

    if (len(total_data['季度']) == 0):
      #print(type(table))
      temp_quarter_name = table.find('tr').find('th')

      for i in range(7):
        total_data['季度'].append(temp_quarter_name.findNext('th').text)
        temp_quarter_name = temp_quarter_name.findNext('th')

    #print(table)

    #print(table.find('td', string="資產總額"))

    for col_name in want_column:
      start_td = table.find('td', string=col_name)

      if (start_td is not None):
        current_td = table.find('td', string=col_name).findNext('td')
        temp_list = [text_to_number(current_td.text)]

        if (idx == 0 or idx == 1):
          for i in range(6):
            current_td = current_td.findNext('td').findNext('td')
            temp_list.append(text_to_number(current_td.text))
        elif (idx == 2):
          for i in range(6):
            current_td = current_td.findNext('td')
            temp_list.append(text_to_number(current_td.text))
        else:
          print('Something wrong?!')

        total_data[col_name] = temp_list
        temp_list.clear  #清空temp_list，給下一個使用
      else:
        continue

  else:
    print('查無此股票代碼，請重新輸入!')
    break

if(company_name != ''):
  print(total_data)
  showResult(total_data,want_column, company_name)








