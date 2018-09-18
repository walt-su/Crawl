# -*- coding: utf-8 -*-
from selenium import webdriver
import re
from datetime import datetime,timedelta
import time
import MySQLdb as mariadb


def GetMatchInfo(Url):
    GetLink = []
    RemoveLink =[]
    Click_check = 0
    GetTime = []
    GetResult = []
    whileloop = 0
    Accu_Index = 0

    conn = mariadb.connect(user = "root", passwd = "1111", db = "soccer")
    cursor = conn.cursor()
    # Get old data from DB in order to avoid getting replicate data
    sql = "select distinct URL from soccer_matchresult where datetime > (curdate()-INTERVAL 60 DAY)" #設定抓3周內的歷史資料
    cursor.execute(sql)
    old_url = list(cursor)
    GetLink_old_data = []
    for i in range(len(old_url)):
        GetLink_old_data.append(old_url[i][0])
    web.get(Url)
    time.sleep(3)
    #從目前的比賽往前推一周(跳一頁), 若要抓歷史記錄, 則這行要取消, 以免抓不到最後一周的資料。
    #web.find_element_by_xpath('//*[@id="date-controller"]/a[1]/span').click()
    #time.sleep(3)
    
    while whileloop==0:     
        #確認有沒有重複  
        try:
            All_Link = web.find_elements_by_xpath('//*[@id="tournament-fixture"]//a[@class="result-1 rc"]') # 抓出每一分頁的Link。
            All_Link_Len = len(All_Link)                                                                    # 實際已比賽完的場數。
            Check_NO_Game = 0

            for i in All_Link:
                Live = i.get_attribute("href").find("Live")
                DataCheck = i.get_attribute("href")[0:(Live+4)]                                             # 用來比對歷史資料。 "+4" 是要包含 "Live" 這四個字。
                GetLink.append(DataCheck)                                                                   # 比對前先存放所有的URL。
                if DataCheck in GetLink_old_data:                                                           # 若資料有在歷史資料中, 則Check_No_Game + 1, 以及把該筆 URL 放到 RemoveLink, 
                    Check_NO_Game += 1                                                                      # 等會用全部資料扣除這些重複的資料後, 再 insert 到 DB
                    RemoveLink.append(DataCheck)                                                            # 用來存放重複的 URL。
            if Check_NO_Game == All_Link_Len or Click_check > 10:                                            # 1)若該分頁所有的資料都已在DB, 則跳出程式結束。 2)若要從頭開始抓, 則設定 Click_check > 50:  
                print ('Break, because there is no new data.')
                break
            
            No_Game_Index = 0                                                                               # 抓取每一場比賽時間/主客隊/比分, 並合併成GetResult。
            for i in web.find_elements_by_xpath('//table[@id="tournament-fixture"]/tbody/tr'):
                if len(re.split('\n| FT ',i.text)) == 1:
                    GetTime = i.text
                elif len(re.split('\n| FT ',i.text)) != 1 and No_Game_Index < All_Link_Len:                 # 如果該分頁的已被記錄的場數(No_Game_Index)多於實際已賽(All_Link_Len)的場數, 則跳到 else, 即跳出迴圈。
                    TempGetResult = [GetLink[Accu_Index]]+[GetTime] + re.split('\n| FT ',i.text)
                    if GetLink[Accu_Index] in RemoveLink:                                                   # 在這把在DB中已有的資料刪除, 只留下DB中沒有的資料。
                        pass 
                    else:
                        GetResult.append( TempGetResult )
                    Accu_Index += 1                                                                         # 因為All_Link是每一分頁的Link累積記錄而成, 所以當換分頁時, 這裡也要用累計次數使得每一場資料可以對應正確的Link。
                    No_Game_Index += 1 
                else:
                    break
            Click_check += 1                                                                                # 若三周內DB沒更新資料, 則最多跑四個迴圈去更新前三周+本周(共四周)的資料。
            print ("GetResult: ", GetResult)
        except Exception as e:
            print ("No current week data.", e)         
        web.find_element_by_xpath('//*[@id="date-controller"]/a[1]/span').click()                           #往前推一周
        time.sleep(5)
    return GetResult

def GetMatchInfo_Insert_DB(InsertValue):
    placeholders = ', '.join(['%s'] * len(InsertValue))
    columns = ', '.join(InsertValue.keys())
    print ("URL:", InsertValue["Url"])
    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('soccer_matchresult', columns, placeholders)
    #print (sql)
    cursor.execute(sql,InsertValue.values())
    conn.commit()
    print ("Insert already")


if __name__ == "__main__":

    conn =  mariadb.connect(user='root',passwd='1111',db='soccer')
    cursor = conn.cursor()
    
    chromeOptions = webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096 }
    chromeOptions.add_experimental_option("prefs", prefs)
    web = webdriver.Chrome("E:\Walt\Python\chromedriver_win32\chromedriver", chrome_options=chromeOptions)
    web.set_page_load_timeout(60)
    Url_Epl = ["https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/7361/England-Premier-League"]
    Url_Lal = ["https://www.whoscored.com/Regions/206/Tournaments/4/Spain-La-Liga"]
    Url_Bun = ["https://www.whoscored.com/Regions/81/Tournaments/3/Germany-Bundesliga"]
    Url_Sea = ["https://www.whoscored.com/Regions/108/Tournaments/5/Italy-Serie-A"]
    Url_Lig = ["https://www.whoscored.com/Regions/74/Tournaments/22/France-Ligue-1"]

    try:
        for Url in Url_Epl + Url_Lal: #+ Url_Bun + Url_Sea + Url_Lig:
            #專門抓歷史資料 會先跳一頁
            GetResult = GetMatchInfo(Url)

            if re.split('/',Url)[4]=='252':
                Type = 'EPL'
            elif re.split('/',Url)[4]=='206':
                Type = 'LaLiga'
            elif re.split('/',Url)[4]=='81':
                Type = 'Germany-Bundesliga'
            elif re.split('/',Url)[4]=='108':
                Type = 'Italy-Serie-A'
            else:
                Type = 'France-Ligue-1'

            for index in range(len(GetResult)):
                Temp = GetResult[index]
                TempScore = re.split(' : ',Temp[4])

                if (re.sub('[1-9]','',Temp[3]) == u'Athletic Bilbao'): #Bilbao 名稱不同, 若以後有類似球隊也要加在這裡。
                    Home = u'Athletic Club'
                else:
                    Home = re.sub('[1-9]','',Temp[3])
                if (re.sub('[1-9]','',Temp[5]) == u'Athletic Bilbao'):
                    Away = u'Athletic Club'
                else:
                    Away = re.sub('[1-9]','',Temp[5])

                datetime_old = datetime.strptime(Temp[1], '%A, %b %d %Y')
                datetime_cor = datetime.strptime(Temp[1] + " " + Temp[2] + ":00", '%A, %b %d %Y %H:%M:%S') + timedelta(hours = 7) # 轉換時間, 因為要和球探網一致。

                InsertValue = {'Url':Temp[0], 'Type': Type, 'Datetime':datetime_cor, 'HomeTeam':Home, 'AwayTeam':Away,\
                               'HomeScore': TempScore[0], 'AwayScore':TempScore[1] }
                print (InsertValue)
                GetMatchInfo_Insert_DB(InsertValue)
    except Exception as e:
        print (Url,'\n', e)

    web.close()
    web.quit()
        
    sql = "delete from soccer_matchresult where rowid not in (select * from (select max(rowid) from soccer_matchresult group by URL,TYPE,DATETIME,HOMETEAM,HOMESCORE,AWAYSCORE,AWAYTEAM ) as t)"
    cursor.execute(sql)

    conn.commit()
    conn.close()

