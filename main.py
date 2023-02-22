#codes were run on google's colab!


# 1.用指令來下載ttf檔(台北黑體之字型檔)
!wget -O taipei_sans_tc_beta.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
  
  
# 2.程式主體
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
#stock_code = input('請輸入股票代碼: ')
stock_code = str(2330)  #測試用，到時候要註記掉

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

#列出所需欄位的資料，之後一次取得
want_column = [
  '資產總額', '存貨', '負債總額', '股東權益總額', '每股淨值(元)', '營業收入', '營業成本', '營業毛利', '營業費用',
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
  investing = list(data['投資活動之淨現金流入(出)'])
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
  
  fig3.yaxis.set_major_locator(MultipleLocator(10)) #設定y軸刻度間距
  #fig3.yaxis.set_major_locator(MaxNLocator(10)) -> 無法多種設定都用上

  operating_income = data['營業利益']
  operating_income.reverse()
  operating_income = np.array(operating_income)
  revenue = data['營業收入']
  revenue.reverse()
  revenue = np.array(revenue)
  operating_margin = operating_income / revenue * 100
  lns1 = fig3.plot(x,operating_margin, color='orange', marker='o', label='營業利益率')


  gross_profit = data['營業毛利']
  gross_profit.reverse()
  gross_profit = np.array(gross_profit)
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


  #plt.ylim(bottom=0)  #上限該如何設定，維持10為間距，且包含整體的最大值? -> OK
  #設定上下臨界值
  fig3.set_ylim([0,int(max(gross_profit_margin))+10])

  fig3_1_interval = max(revenue)/((int(max(gross_profit_margin))+10)/10)
  fig3_1.set_ylim(bottom=0,top=max(revenue)+fig3_1_interval)


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



  fig4.set_ylim([0,max(return_on_equity)+max(return_on_equity)/7])
  fig4.legend(bbox_to_anchor=(1,0.7), loc='upper left')
  fig4.grid(axis='y')
  plt.title('報酬率(' + company_name + ')', fontsize=18)
  fig4.set_ylabel('%')
  plt.show()


  #在畫面上呈現財報(用print的方式)
  #轉換成表格的形式
  #經過上面的操作，部分的list已經被轉換順序了 -> 先把剩下未轉換順序的都轉好，再來增加新內容，最後輸出
  inventory=data['存貨']
  inventory.reverse()
  new_worth=data['每股淨值(元)']
  new_worth.reverse()
  operating_cost=data['營業成本']
  operating_cost.reverse()
  operating_expenses=data['營業費用']
  operating_expenses.reverse()
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


  answer = input('\n是否要輸出成excel檔?(Y/N):')
  if(answer == 'Y' or answer == 'y'):
    outputFile()
    print('輸出完成!')
  else:
    print('程式結束')
  



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

showResult(dataa, want_column, 'company_name')

#============================== MAIN FUNCTION ==============================
"""
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

"""




