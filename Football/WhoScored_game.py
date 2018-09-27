# -*- coding: utf-8 -*-
import re
import time
from selenium import webdriver
from datetime import datetime,timedelta
import MySQLdb as mariadb


def GetMatchInfo(Url):
    chromeOptions = webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096 }
    chromeOptions.add_experimental_option("prefs", prefs)
    web = webdriver.Chrome("E:\Walt\Python\chromedriver_win32\chromedriver", chrome_options=chromeOptions)
    web.set_page_load_timeout(60)

    GetLink = []
    RemoveLink =[]
    Click_check = 0
    GetTime = []
    GetResult = []
    Accu_Index = 0

    sql = "select distinct URL from soccer_matchresult where datetime > (curdate()-INTERVAL 60 DAY)"        # 設定抓3周內的歷史資料
    cursor.execute(sql)
    old_url = list(cursor)
    GetLink_old_data = []
    for i in range(len(old_url)):
        GetLink_old_data.append(old_url[i][0])
    web.get(Url)
    #從目前的比賽往前推一周(跳一頁), 若要抓歷史記錄, 則這行要取消, 以免抓不到最後一周的資料。
    #web.find_element_by_xpath('//*[@id="date-controller"]/a[1]/span').click()   
    while True:     
        try:
            #All_Link = web.find_elements_by_xpath('//*[@id="tournament-fixture"]//a[@class="result-1 rc"]')
            All_Link_temp = web.find_elements_by_xpath('//*[@id="tournament-fixture"]//td[@class="result"]/a')  
            All_Link = [i for i in All_Link_temp if i.get_attribute("class") != "result-4 rc"]              # 第一次抓出每一分頁的Link。
            if len(All_Link) == 0:                                                                          # 如果第一頁沒比賽, 就按下一頁, 並重新計算未開打比賽
                web.find_element_by_xpath('//*[@id="date-controller"]/a[1]/span').click()                   
                time.sleep(3)
                All_Link_temp = web.find_elements_by_xpath('//*[@id="tournament-fixture"]//td[@class="result"]/a')
                All_Link = [i for i in All_Link_temp if i.get_attribute("class") != "result-4 rc"]          # 去掉還沒開打的比賽(result-4 rc)                
            All_Link_Len = len(All_Link)                                                                    # 實際已比賽完的場數。

            # 針對Link做處理
            Check_NO_Game = 0                                                                               # 用來確認該周DB已抓了幾場          
            for i in All_Link:
                Live = i.get_attribute("href").find("Live")
                if Live == -1:
                    Live = i.get_attribute("href").find("Show")                                             # 若是延賽，就用"Show"
                DataCheck = i.get_attribute("href")[0:(Live+4)]                                             # 用來比對歷史資料。 "+4" 是要包含 "Live" 這四個字。
                GetLink.append(DataCheck)                                                                   # 比對前先存放所有的URL。
                if DataCheck in GetLink_old_data:                                                           # 若資料有在歷史資料中, 則Check_No_Game + 1, 以及把該筆 URL 放到 RemoveLink, 
                    Check_NO_Game += 1                                                                      # 等會用全部資料扣除這些重複的資料後, 再 insert 到 DB
                    RemoveLink.append(DataCheck)                                                            # 用來存放重複的 URL。
            if  All_Link_Len == Check_NO_Game or Click_check > 6:                                           # 若該分頁所有的資料都已在DB, 則跳出程式結束。 若要從頭開始抓, 則設定 Click_check > 39:  
                break
            for i in GetLink:
                print(i)
            
            # 開始抓資料
            No_Game_Index = 0                                                                               # 抓取每一場比賽時間/主客隊/比分, 並合併成GetResult。
            for i in web.find_elements_by_xpath('//table[@id="tournament-fixture"]/tbody/tr'):
                if re.search(' Post ',i.text) == None:                                                      # 如果有延期的, 將FT改成Post去分段
                    row_data = re.split('\n| FT ',i.text)
                else:
                    row_data = re.split('\n| Post ',i.text)
                
                if len(row_data) == 1:                                                                      # 網頁上的時間列得到後為一個List, 內容為時間
                    GetTime = i.text
                elif len(row_data) != 1 and No_Game_Index < All_Link_Len:                                   # 如果該分頁的已被記錄的場數(No_Game_Index)多於實際已賽(All_Link_Len)的場數, 則跳到 else, 即跳出迴圈。
                    TempGetResult = [GetLink[Accu_Index]]+[GetTime] + row_data
                    if GetLink[Accu_Index] in RemoveLink:                                                   # 在這把在DB中已有的資料刪除, 只留下DB中沒有的資料。
                        pass 
                    else:
                        GetResult.append(TempGetResult)
                    Accu_Index += 1                                                                         # 因為All_Link是每一分頁的Link累積記錄而成, 所以當換分頁時, 這裡也要用累計次數使得每一場資料可以對應正確的Link。
                    No_Game_Index += 1 
                else:
                    break
            Click_check += 1                                                                                # 若三周內DB沒更新資料, 則最多跑四個迴圈去更新前三周+本周(共四周)的資料。
        except Exception as e:
            print ("No current week data.", e)         
        web.find_element_by_xpath('//*[@id="date-controller"]/a[1]/span').click()                           # 往前推一周
        time.sleep(3)
    web.close()
    web.quit()
    return GetResult

def GetMatchInfo_Insert_DB(InsertValue):
    placeholders = ', '.join(['%s'] * len(InsertValue))
    columns = ', '.join(InsertValue.keys())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('soccer_matchresult', columns, placeholders)
    cursor.execute(sql,InsertValue.values())

def GetType(Url):
    if re.split('/',Url)[4]=='252':
        Type = 'EPL'
    elif re.split('/',Url)[4]=='206':
        Type = 'LaLiga'
    elif re.split('/',Url)[4]=='81':
        Type = 'Bundesliga'
    elif re.split('/',Url)[4]=='108':
        Type = 'SerieA'
    elif re.split('/',Url)[4]=='74':
        Type = 'Ligue1'
    else:
        Type = "Other"
    return Type


if __name__ == "__main__":

    conn =  mariadb.connect(user='root',passwd='1111',db='soccer')
    cursor = conn.cursor()

    Url_Epl = ["https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/7361/England-Premier-League"]
    Url_Lal = ["https://www.whoscored.com/Regions/206/Tournaments/4/Spain-La-Liga"]
    Url_Bun = ["https://www.whoscored.com/Regions/81/Tournaments/3/Germany-Bundesliga"]
    Url_Sea = ["https://www.whoscored.com/Regions/108/Tournaments/5/Italy-Serie-A"]
    Url_Lig = ["https://www.whoscored.com/Regions/74/Tournaments/22/France-Ligue-1"]

    for Url in Url_Epl:# + Url_Lal + Url_Bun + Url_Sea + Url_Lig:
        print("Url:", GetType(Url))
        GameResults = GetMatchInfo(Url)

        if len(GameResults) != 0:
            for game in GameResults:
                if game[4] == "vs":
                    TempScore = [None,None]    
                else:
                    TempScore = re.split(' : ',game[4])

                if (re.sub('[1-9]','',game[3]) == u'Athletic Bilbao'):                                      # Bilbao 名稱不同, 若以後有類似球隊也要加在這裡。
                    Home = u'Athletic Club'
                else:
                    Home = re.sub('[1-9]','',game[3])
                if (re.sub('[1-9]','',game[5]) == u'Athletic Bilbao'):
                    Away = u'Athletic Club'
                else:
                    Away = re.sub('[1-9]','',game[5])

                datetime_old = datetime.strptime(game[1], '%A, %b %d %Y')
                datetime_cor = datetime.strptime(game[1] + " " + game[2] + ":00", '%A, %b %d %Y %H:%M:%S')\
                                                 + timedelta(hours = 7)                                      # 轉換時間, 因為要和球探網一致。

                InsertValue = {'Url':game[0], 'Type': GetType(Url), 'Datetime':datetime_cor, 'HomeTeam':Home,\
                               'AwayTeam':Away, 'HomeScore': TempScore[0], 'AwayScore':TempScore[1] }
                GetMatchInfo_Insert_DB(InsertValue)
                conn.commit()
            print("Insert_DB OK.")
        else:
            print ('There is no new data in', GetType(Url))
       
    sql = "delete from soccer_matchresult where rowid not in (select * from (select max(rowid) from \
           soccer_matchresult group by URL,TYPE,DATETIME,HOMETEAM,HOMESCORE,AWAYSCORE,AWAYTEAM ) as t)"
    cursor.execute(sql)
    print("Remove duplicates OK.")

    conn.commit()
    conn.close()

