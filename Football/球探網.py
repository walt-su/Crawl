# -*- coding: utf-8 -*-
from datetime import datetime
import time
import requests
import re
from selenium import webdriver
import MySQLdb as mariadb 
import pyodbc

##### Insert DB
def Insert_MySQL(InsertValue):
    placeholders = ', '.join(['%s'] * len(InsertValue))
    columns = ', '.join(InsertValue.keys())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('soccer_matchrate_add', columns, placeholders)
    cursor_mYsql.execute(sql,InsertValue.values())

def Insert_MsSQL(InsertValue):
    placeholders = ', '.join(['?'] * len(InsertValue))
    columns = ', '.join(InsertValue.keys())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('soccer_matchrate_add', columns, placeholders)
    cursor_MSsql.execute(sql,list(InsertValue.values()))

##### Check type
def CheckType(url):
    TypeNumber = re.split('/|-|\.',url)[9]
    if TypeNumber=='s36':
        TypeNumber='EPL'
    elif TypeNumber=='s31':
        TypeNumber='LaLiga'
    elif TypeNumber=='s8':
        TypeNumber='Bundesliga'
    elif TypeNumber=='s34':
        TypeNumber='SerieA'
    elif TypeNumber=='s11':
        TypeNumber='Ligue1'
    return TypeNumber

##### Game data
def crawl_game_data(url):
    headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6",
    "Connection": "keep-alive",
    "Cookie": "UM_distinctid=165a7f31d8f508-0ff2df74422a83-9393265-1fa400-165a7f31d911be; detailCookie=null; CNZZDATA1261430177=693195137-1536117952-%7C1536740950",
    "Host": "zq.win007.com",
    "Referer": "http://zq.win007.com/cn/League/2017-2018/36.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
    }

    while True:
        try:
            print("Url:", url)    
            response = requests.get(url, headers=headers)
            stat = response.status_code
        except:
            pass
            time.sleep(3)
            print("Re-crawl")
        else:
            break
    team_name = {}
    games = []
    re_1 = re.compile("\"([\w]+)\"")                                          # 用來取得周次 -> "R_1"
    re_2 = re.compile("R_\d")                                                 # 用來取得所有比賽的周數
    row_data = response.text.split("];")
    no_week = 0
    for text in row_data:
        if re_2.search(text) != None:
            no_week += 1   
    print("Type: ", CheckType(url))
    print("No. of Weeks: ", no_week)
    
    teams_data = row_data[1].split(" = ")                                     # 從第二列取得隊名資料
    teams = teams_data[1].strip("[]").split("],[")
    for team in teams:
        temp = team.split(",")
        team_name[temp[0]] = temp[1:7]

    for week in row_data[2:(no_week+2)]:                                      # 第三列起的每一列代表每一周的比賽資料, 前兩列是 "說明" 以及 "中英隊名"
        week_data = week.split(" = ")
        week_round = re_1.search(week_data[0]).group(1)                       # 取得周次     
        week_games = week_data[1].strip("[]").split("],[")                    # 處理每周比賽資料
        for game in week_games:
            game_data = game.split(",")
            for i in range(len(game_data)):
                game_data[i] = game_data[i].strip("'")
            Euro_url = "http://1x2.win007.com/oddslist/"+game_data[0]+".htm"  # 歐盤資料網址
            game_data.append(Euro_url.rstrip())                               # 記入歐盤資料網址, str.rstrip 是去掉空格
            game_data.append(week_round)                                      # 記入周別資料
            game_data.append(team_name[game_data[4]][2].strip("'"))           # 取得主隊隊名(game_data[4]), [1] 是繁體, [2] 是英文
            game_data.append(team_name[game_data[5]][2].strip("'"))           # 取得各隊隊名(game_data[5]), [1] 是繁體, [2] 是英文
            games.append(game_data)
    
    games_return = [i for i in games if i[8] != ""]                           # 只留歷史記錄以及未來一周的比賽, i[8] 是主隊當周的名次
    
    return games_return

##### Odds & Kelly data
def crawl_odds_kelly(Euro_url):
    chromeOptions = webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096 }
    chromeOptions.add_experimental_option("prefs", prefs)
    web = webdriver.Chrome("E:\Walt\Python\chromedriver_win32\chromedriver", chrome_options=chromeOptions)
    Company = []
    H_Rate     = []; D_Rate    = []; A_Rate    = []                           # 賠率 365
    H_WinRate  = []; D_WinRate = []; A_WinRate = []                           # 勝率 365
    ReturnRate = [];                                                          # 返還率 365

    H_Rate_pin     = []; D_Rate_pin    = []; A_Rate_pin    = []               # for pinnacle
    H_WinRate_pin  = []; D_WinRate_pin = []; A_WinRate_pin = []
    ReturnRate_pin = [];

    H_Rate_fair     = []; D_Rate_fair    = []; A_Rate_fair    = []            # for Betfair
    H_WinRate_fair  = []; D_WinRate_fair = []; A_WinRate_fair = []
    ReturnRate_fair = [];

    H_Rate_hill     = []; D_Rate_hill    = []; A_Rate_hill    = []            # for William Hill
    H_WinRate_hill  = []; D_WinRate_hill = []; A_WinRate_hill = []
    ReturnRate_hill = [];

    H_Rate_high = []; D_Rate_high = []; A_Rate_high = []                      # for overall
    H_Rate_low  = []; D_Rate_low  = []; A_Rate_low  = []
    H_Rate_mean = []; D_Rate_mean = []; A_Rate_mean = []
    H_WinRate_high = []; D_WinRate_high = []; A_WinRate_high = []    
    H_WinRate_low  = []; D_WinRate_low  = []; A_WinRate_low  = []
    H_WinRate_mean = []; D_WinRate_mean = []; A_WinRate_mean = []

    H_Kelly = []; D_Kelly = []; A_Kelly = []                                  # Kelly index    

    for i in Euro_url:  
        web.get(i)
        time.sleep(4)
        web.find_element_by_xpath('//*[@id="sel_showType"]/option[2]').click()                 #指定初盤
        time.sleep(4)
        try:            # for 365
            Temp = re.split(' ',web.find_element_by_xpath('//tr[@id="oddstr_281"]').text)      # Bet365 id 代碼是 oddstr_281
            Company.append((Temp[0]+Temp[1][0:3])) 
            H_Rate.append(Temp[2]);
            D_Rate.append(Temp[3])
            A_Rate.append(Temp[4])
            H_WinRate.append(Temp[5])
            D_WinRate.append(Temp[6])
            A_WinRate.append(Temp[7])
            ReturnRate.append(Temp[8])
            H_Kelly.append(Temp[9])
            D_Kelly.append(Temp[10])
            A_Kelly.append(Temp[11])
        except:
            Company.append(None)
            H_Rate.append(None)
            D_Rate.append(None)
            A_Rate.append(None)
            H_WinRate.append(None)
            D_WinRate.append(None)
            A_WinRate.append(None)
            ReturnRate.append(None)
            H_Kelly.append(None)
            D_Kelly.append(None)
            A_Kelly.append(None)
        try:            # for Pin
            Temp_pin  = re.split(' ',web.find_element_by_xpath('//tr[@id="oddstr_177"]').text) # Pinnacle id 代碼是 oddstr_177
            H_Rate_pin.append(Temp_pin[1])
            D_Rate_pin.append(Temp_pin[2])
            A_Rate_pin.append(Temp_pin[3])
            H_WinRate_pin.append(Temp_pin[4])
            D_WinRate_pin.append(Temp_pin[5])
            A_WinRate_pin.append(Temp_pin[6])
            ReturnRate_pin.append(Temp_pin[7])
        except:
            H_Rate_pin.append(None)
            D_Rate_pin.append(None)
            A_Rate_pin.append(None)
            H_WinRate_pin.append(None)
            D_WinRate_pin.append(None)
            A_WinRate_pin.append(None)
            ReturnRate_pin.append(None)
        try:       # for fair
            Temp_fair = re.split(' ',web.find_element_by_xpath('//tr[@id="oddstr_2"]').text)   # Betfair id 代碼是 oddstr_2
            H_Rate_fair.append(Temp_fair[1])
            D_Rate_fair.append(Temp_fair[2])
            A_Rate_fair.append(Temp_fair[3])
            H_WinRate_fair.append(Temp_fair[4])
            D_WinRate_fair.append(Temp_fair[5])
            A_WinRate_fair.append(Temp_fair[6])
            ReturnRate_fair.append(Temp_fair[7])
        except:
            H_Rate_fair.append(None)
            D_Rate_fair.append(None)
            A_Rate_fair.append(None)
            H_WinRate_fair.append(None)
            D_WinRate_fair.append(None)
            A_WinRate_fair.append(None)
            ReturnRate_fair.append(None)
        try:       # for hill
            Temp_hill = re.split(' ',web.find_element_by_xpath('//tr[@id="oddstr_115"]').text) # WilliamHill id 代碼是 oddstr_115
            H_Rate_hill.append(Temp_hill[1])
            D_Rate_hill.append(Temp_hill[2])
            A_Rate_hill.append(Temp_hill[3])
            H_WinRate_hill.append(Temp_hill[4])
            D_WinRate_hill.append(Temp_hill[5])
            A_WinRate_hill.append(Temp_hill[6])
            ReturnRate_hill.append(Temp_hill[7])
        except:
            H_Rate_hill.append(None)
            D_Rate_hill.append(None)
            A_Rate_hill.append(None)
            H_WinRate_hill.append(None)
            D_WinRate_hill.append(None)
            A_WinRate_hill.append(None)
            ReturnRate_hill.append(None)
        try:    # for overall
            Temp_high = re.split(' ',web.find_element_by_xpath('//tr[@id="highFObj"]').text) 
            Temp_low  = re.split(' ',web.find_element_by_xpath('//tr[@id="lowFObj"]').text)  
            Temp_mean = re.split(' ',web.find_element_by_xpath('//tr[@id="avgFObj"]').text)  
            H_Rate_high.append(Temp_high[2])
            D_Rate_high.append(Temp_high[3])
            A_Rate_high.append(Temp_high[4])
            H_WinRate_high.append(Temp_high[5])
            D_WinRate_high.append(Temp_high[6])
            A_WinRate_high.append(Temp_high[7])
            H_Rate_low.append(Temp_low[1])
            D_Rate_low.append(Temp_low[2])
            A_Rate_low.append(Temp_low[3])
            H_WinRate_low.append(Temp_low[4])
            D_WinRate_low.append(Temp_low[5])
            A_WinRate_low.append(Temp_low[6])
            H_Rate_mean.append(Temp_mean[1])
            D_Rate_mean.append(Temp_mean[2])
            A_Rate_mean.append(Temp_mean[3])            
            H_WinRate_mean.append(Temp_mean[4])
            D_WinRate_mean.append(Temp_mean[5])
            A_WinRate_mean.append(Temp_mean[6])
        except:
            H_Rate_high.append(None)
            D_Rate_high.append(None)
            A_Rate_high.append(None)
            H_WinRate_high.append(None)
            D_WinRate_high.append(None)
            A_WinRate_high.append(None)
            H_Rate_low.append(None)
            D_Rate_low.append(None)
            A_Rate_low.append(None)
            H_WinRate_low.append(None)
            D_WinRate_low.append(None)
            A_WinRate_low.append(None)
            H_Rate_mean.append(None)
            D_Rate_mean.append(None)
            A_Rate_mean.append(None)
            H_WinRate_mean.append(None)
            D_WinRate_mean.append(None)
            A_WinRate_mean.append(None)
    web.close()
    web.quit()
    return  Company,H_Rate,D_Rate,A_Rate,H_WinRate,D_WinRate,A_WinRate,ReturnRate,H_Kelly,D_Kelly,A_Kelly\
            ,H_Rate_pin, D_Rate_pin, A_Rate_pin, H_WinRate_pin, D_WinRate_pin, A_WinRate_pin, ReturnRate_pin\
            ,H_Rate_fair,D_Rate_fair,A_Rate_fair,H_WinRate_fair,D_WinRate_fair,A_WinRate_fair,ReturnRate_fair\
            ,H_Rate_hill,D_Rate_hill,A_Rate_hill,H_WinRate_hill,D_WinRate_hill,A_WinRate_hill,ReturnRate_hill\
            ,H_Rate_high,D_Rate_high,A_Rate_high,H_WinRate_high,D_WinRate_high,A_WinRate_high\
            ,H_Rate_low, D_Rate_low, A_Rate_low, H_WinRate_low, D_WinRate_low, A_WinRate_low\
            ,H_Rate_mean,D_Rate_mean,A_Rate_mean,H_WinRate_mean,D_WinRate_mean,A_WinRate_mean           # 50 features

if __name__ == '__main__': 
    
    conn_mYsql = mariadb.connect(user="root", passwd="1111", db="soccer", charset="utf8")                                                   # for MySQL
    cursor_mYsql = conn_mYsql.cursor()

    _server = "tcp:sqlservertest123456.database.windows.net"
    _database = "Soccer"
    _uid = "kevin"
    _pwd = "qwert@WSX"
    #conn_MSsql = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+_server+';DATABASE='+_database+';UID='+_uid+';PWD='+_pwd)  # for MSSQL
    #cursor_MSsql = conn_MSsql.cursor()
    
    _date = datetime.now()
    version = str(_date.year) + str(format(_date.month, "02d")) + str(format(_date.day, "02d")) + str(format(_date.hour, "02d"))
    url = [#"http://zq.win007.com/jsData/matchResult/2018-2019/s36.js?version="+version
           "http://zq.win007.com/jsData/matchResult/2015-2016/s31.js?version="+version
           #"http://zq.win007.com/jsData/matchResult/2017-2018/s8.js?version=" +version,
           #"http://zq.win007.com/jsData/matchResult/2017-2018/s34.js?version="+version,
           #"http://zq.win007.com/jsData/matchResult/2017-2018/s11.js?version="+version
          ]
    OverAll_time = datetime.now()
    for u in url:
        # 1) Get basic game data
        games = crawl_game_data(u)
        print("Step1: Basic game data OK.")
    
        # 2) Get odds & kelly data
        game_index = [[0, 70], [70, 140], [140, 210], [210, 290], [290, len(games)]]   # 設定抓取的賽次範圍, 避免被封鎖一次抓不完
        #game_index = [[70, 140],[140, 210], [210, 290], [290, len(games)]]             # 設定抓取的賽次範圍, 避免被封鎖一次抓不完
        #game_index = [[0, 70]]
        for l in game_index:
            EachRound_time = datetime.now()
            games_temp = games[l[0]:l[1]]
            print("Step2: Crawled games from ", l[0], "to", l[1])                    

            link_euro = []                                  
            for game in games_temp:
                link_euro.append(game[23])                                              # Game data 共有38個欄位, Link 在game[23], 2013-2014球季在game[21]
            Company,H_Rate,D_Rate,A_Rate,H_WinRate,D_WinRate,A_WinRate,ReturnRate,H_Kelly,D_Kelly,A_Kelly\
            ,H_Rate_pin, D_Rate_pin, A_Rate_pin, H_WinRate_pin, D_WinRate_pin, A_WinRate_pin, ReturnRate_pin\
            ,H_Rate_fair,D_Rate_fair,A_Rate_fair,H_WinRate_fair,D_WinRate_fair,A_WinRate_fair,ReturnRate_fair\
            ,H_Rate_hill,D_Rate_hill,A_Rate_hill,H_WinRate_hill,D_WinRate_hill,A_WinRate_hill,ReturnRate_hill\
            ,H_Rate_high,D_Rate_high,A_Rate_high,H_WinRate_high,D_WinRate_high,A_WinRate_high\
            ,H_Rate_low, D_Rate_low, A_Rate_low, H_WinRate_low, D_WinRate_low, A_WinRate_low\
            ,H_Rate_mean,D_Rate_mean,A_Rate_mean,H_WinRate_mean,D_WinRate_mean,A_WinRate_mean = crawl_odds_kelly(link_euro)
            print("Step2: Odds & Kelly data OK.")
            
            # 3) Insert to DB
            for i in range(len(games_temp)):                  
                Value = {'Type':CheckType(u),
                         'Datetime':datetime.strptime(games_temp[i][3],'%Y-%m-%d %H:%M'),
                         'HomeTeam':games_temp[i][4],
                         'AwayTeam':games_temp[i][5],
                         'Score':games_temp[i][6],
                         'Score_h':games_temp[i][7],
                         'HomeRank':games_temp[i][8],
                         'AwayRank':games_temp[i][9],             
                         'Handicap_a':games_temp[i][10],
                         'Handicap_h':games_temp[i][11],
                         'Score_sum_a':games_temp[i][12],
                         'Score_sum_h':games_temp[i][13],
                         'EuroIndex':games_temp[i][15],
                         'HomeRed':games_temp[i][18],
                         'AwayRed':games_temp[i][19],
                         'Unknown':games_temp[i][20],
                         'EuroURL':games_temp[i][23],                                  # 2013-2014球季在game[21], others is game[23]
                         'GameRound':games_temp[i][24],                                # 2013-2014球季在game[22], others is game[24]
                         'HomeName':games_temp[i][25],                                 # 2013-2014球季在game[23], others is game[25]
                         'AwayName':games_temp[i][26],                                 # 2013-2014球季在game[24], others is game[26]
                         # odds & kelly
                         'Company':Company[i],
                         'HRate':H_Rate[i],
                         'DRate':D_Rate[i],
                         'ARate':A_Rate[i],
                         'HWinRate':H_WinRate[i],
                         'DWinRate':D_WinRate[i],
                         'AWinRate':A_WinRate[i],
                         'ReturnRate':ReturnRate[i],
                         'HKelly':H_Kelly[i],
                         'DKelly':D_Kelly[i],
                         'AKelly':A_Kelly[i],
                         'HRate_pin':H_Rate_pin[i],
                         'DRate_pin':D_Rate_pin[i],
                         'ARate_pin':A_Rate_pin[i],
                         'HWinRate_pin':H_WinRate_pin[i],
                         'DWinRate_pin':D_WinRate_pin[i],
                         'AWinRate_pin':A_WinRate_pin[i],
                         'ReturnRate_pin':ReturnRate_pin[i],
                         'HRate_fair':H_Rate_fair[i],
                         'DRate_fair':D_Rate_fair[i],
                         'ARate_fair':A_Rate_fair[i],
                         'HWinRate_fair':H_WinRate_fair[i],
                         'DWinRate_fair':D_WinRate_fair[i],
                         'AWinRate_fair':A_WinRate_fair[i],
                         'ReturnRate_fair':ReturnRate_fair[i],
                         'HRate_hill':H_Rate_hill[i],
                         'DRate_hill':D_Rate_hill[i],
                         'ARate_hill':A_Rate_hill[i],
                         'HWinRate_hill':H_WinRate_hill[i],
                         'DWinRate_hill':D_WinRate_hill[i],
                         'AWinRate_hill':A_WinRate_hill[i],
                         'ReturnRate_hill':ReturnRate_hill[i],
                         'HRate_high':H_Rate_high[i],
                         'DRate_high':D_Rate_high[i],
                         'ARate_high':A_Rate_high[i],
                         'HRate_low':H_Rate_low[i],
                         'DRate_low':D_Rate_low[i],
                         'ARate_low':A_Rate_low[i],
                         'HRate_mean':H_Rate_mean[i],
                         'DRate_mean':D_Rate_mean[i],
                         'ARate_mean':A_Rate_mean[i],
                         'HWinRate_high':H_WinRate_high[i],
                         'DWinRate_high':D_WinRate_high[i],
                         'AWinRate_high':A_WinRate_high[i],
                         'HWinRate_low':H_WinRate_low[i],
                         'DWinRate_low':D_WinRate_low[i],
                         'AWinRate_low':A_WinRate_low[i],
                         'HWinRate_mean':H_WinRate_mean[i],
                         'DWinRate_mean':D_WinRate_mean[i],
                         'AWinRate_mean':A_WinRate_mean[i]}  
                print(Value)
                Insert_MySQL(Value)
                conn_mYsql.commit()
                #Insert_MsSQL(Value)
                #conn_MSsql.commit()
            print("Step3: Insert_DB OK.")
            
            # 4) Remove duplicates 
            sql_mYsql = "delete from soccer_matchrate_add where rowid not in (select * from (select max(rowid)\
                         from soccer_matchrate_add group by TYPE,DATETIME,HOMETEAM,AWAYTEAM,EuroURL) as t)"            # for MySQL
            cursor_mYsql.execute(sql_mYsql)
            conn_mYsql.commit()

            sql_MSsql = "delete from soccer_matchrate_add where rowid not in (select max(rowid)\
                         from soccer_matchrate_add group by TYPE,DATETIME,HOMETEAM,AWAYTEAM,EuroURL)"                  # for MsSQL
            #cursor_MSsql.execute(sql_MSsql)
            #conn_MSsql.commit()            

            print ("Step4: Remove duplicates OK.")
            print("Time of this round: ", datetime.now() - EachRound_time)
            time.sleep(120)
        time.sleep(180)
    conn_mYsql.close()
    #conn_MSsql.close()

    print("Time of OverAll: ", datetime.now() - OverAll_time)
    print("All URLs are done.")

