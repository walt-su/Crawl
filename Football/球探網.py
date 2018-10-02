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
    cursor.execute(sql,InsertValue.values())


def Insert_MsSQL(InsertValue):
    placeholders = ', '.join(['?'] * len(InsertValue))
    columns = ', '.join(InsertValue.keys())
    #sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('soccer_matchrate_add', columns, placeholders)
    sql = "INSERT INTO soccer_matchrate_add ( Type, Datetime, HomeTeam, AwayTeam, Score, Score_h, HomeRank, AwayRank, Handicap_a, Handicap_h, Score_sum_a, Score_sum_h, EuroIndex, HomeRed, AwayRed, Unknown, EuroURL, GameRound, HomeName, AwayName, Company, HRate, DRate, ARate, HWinRate, DWinRate, AWinRate, ReturnRate, HKelly, DKelly, AKelly )\
     VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )"
    a = InsertValue
    cursor.execute(sql,a["Type"], a["Datetime"],a["HomeTeam"],a["AwayTeam"],a["Score"],a["Score_h"],a["HomeRank"],a["AwayRank"],a["Handicap_a"],a["Handicap_h"],a["Score_sum_a"],a["Score_sum_h"],a["EuroIndex"],\
        a["HomeRed"],a["AwayRed"],a["Unknown"],a["EuroURL"],a["GameRound"],a["HomeName"],a["AwayName"],a["Company"],a["HRate"],a["DRate"],a["ARate"],a["HWinRate"],a["DWinRate"],a["AWinRate"],a["ReturnRate"],\
        a["HKelly"],a["DKelly"],a["AKelly"])

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
    H_Rate = []; D_Rate = []; A_Rate = []                                     #賠率
    H_WinRate = []; D_WinRate = []; A_WinRate = []                            #勝率
    ReturnRate = []                                                           #返還率
    H_Kelly = []; D_Kelly = []; A_Kelly = []                                  #Kelly index   
    
    for i in Euro_url:  
        try :
            web.get(i)
            time.sleep(4)
            web.find_element_by_xpath('//*[@id="sel_showType"]/option[2]').click()        #指定初盤
            time.sleep(4)
            Temp = re.split(' ',web.find_element_by_xpath('//tr[@id="oddstr_281"]').text) # Bet365 id 代碼是 oddstr_281
            Company.append((Temp[0]+Temp[1][0:3])) 
            H_Rate.append(Temp[2])
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
            Company.append("")
            H_Rate.append("")
            D_Rate.append("")
            A_Rate.append("")
            H_WinRate.append("")
            D_WinRate.append("")
            A_WinRate.append("")
            ReturnRate.append("")
            H_Kelly.append("")
            D_Kelly.append("")
            A_Kelly.append("")
    web.close()
    web.quit()
    return Company,H_Rate,D_Rate,A_Rate,H_WinRate,D_WinRate,A_WinRate,ReturnRate,H_Kelly,D_Kelly,A_Kelly


if __name__ == '__main__': 
    
    #conn = mariadb.connect(user="root", passwd="1111", db="soccer", charset="utf8")                                                  # for MySQL
    #cursor = conn.cursor()

    _server = "tcp:sqlservertest123456.database.windows.net"
    _database = "Soccer"
    _uid = "kevin"
    _pwd = "qwert@WSX"
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+_server+';DATABASE='+_database+';UID='+_uid+';PWD='+_pwd)  # for MSSQL
    cursor = conn.cursor()
    
    _date = datetime.now()
    version = str(_date.year) + str(format(_date.month, "02d")) + str(format(_date.day, "02d")) + str(format(_date.hour, "02d"))
    url = [#"http://zq.win007.com/jsData/matchResult/2018-2019/s36.js?version="+version,
           "http://zq.win007.com/jsData/matchResult/2018-2019/s31.js?version="+version
           #"http://zq.win007.com/jsData/matchResult/2017-2018/s8.js?version=" +version
           #"http://zq.win007.com/jsData/matchResult/2017-2018/s34.js?version="+version
           #"http://zq.win007.com/jsData/matchResult/2017-2018/s11.js?version="+version
          ]
    OverAll_time = datetime.now()
    for u in url:
        # 1) Get basic game data
        games = crawl_game_data(u)
        print("Step1: Basic game data OK.")
    
        # 2) Get odds & kelly data
        #game_index = [[0, 70], [70, 140], [140, 210], [210, 290], [290, len(games)]]  # 設定抓取的賽次範圍, 避免被封鎖一次抓不完
        #game_index = [[70, 140],[140, 210], [210, 290], [290, len(games)]]            # 設定抓取的賽次範圍, 避免被封鎖一次抓不完
        game_index = [[0, len(games)]]
        for l in game_index:
            EachRound_time = datetime.now()
            games_temp = games[l[0]:l[1]]
            print("Step2: Crawled games from ", l[0], "to", l[1])                    

            link_euro = []                                  
            for game in games_temp:
                link_euro.append(game[23])                                             # Game data 共有27個欄位, Link 在第24個, 2013-2014球季在第24個
            Company,H_Rate,D_Rate,A_Rate,H_WinRate,D_WinRate,A_WinRate,ReturnRate,H_Kelly,D_Kelly,A_Kelly = crawl_odds_kelly(link_euro)
            print("Step2: Odds & Kelly data OK.")
            
            # 3) Insert to DB
            for i in range(len(games_temp)): 
                #print("Homename:", games_temp[i])                     
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
                         'EuroURL':games_temp[i][23],                                  # 2013-2014球季在第24個
                         'GameRound':games_temp[i][24],                                # 2013-2014球季在第25個
                         'HomeName':games_temp[i][25],                                 # 2013-2014球季在第26個
                         'AwayName':games_temp[i][26],                                 # 2013-2014球季在第27個
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
                         'AKelly':A_Kelly[i]}  
                #Insert_MySQL(Value)
                Insert_MsSQL(Value)
                conn.commit()
            print("Step3: Insert_DB OK.")
            
            # 4) Remove duplicates 
            #sql = "delete from soccer_matchrate_add where rowid not in (select * from (select max(rowid) \     # for MySQL
            #       from soccer_matchrate_add group by TYPE,DATETIME,HOMETEAM,AWAYTEAM,EuroURL) as t)"          
            sql = "delete from soccer_matchrate_add where rowid not in (select max(rowid) \
                   from soccer_matchrate_add group by TYPE,DATETIME,HOMETEAM,AWAYTEAM,EuroURL)"                  # for MsSQL
            cursor.execute(sql)
            conn.commit()
            print ("Step4: Remove duplicates OK.")
            print("Time of this round: ", datetime.now() - EachRound_time)
            time.sleep(120)
        time.sleep(180)
    conn.close()
    print("Time of OverAll: ", datetime.now() - OverAll_time)
    print("All URLs are done.")

