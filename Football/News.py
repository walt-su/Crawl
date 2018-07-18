# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import MySQLdb as mariadb

conn =  mariadb.connect(user='root',passwd='',db='NEWS',charset="utf8")
cursor = conn.cursor()

Link_All = []
Title_1 = []
Title_2 = []
Type = []
Author = []
_Date = []
Content = []
    
def Insert_DB(InsertValue):
    placeholders = ', '.join(['%s'] * len(InsertValue))
    columns = ', '.join(InsertValue.keys())
    print ("placeholders:", placeholders, "columns:", columns)
    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('sports_news', columns, placeholders)
    print (sql)
    cursor.execute(sql,InsertValue.values())
    conn.commit()
    print ("Insert already")

def find_2nd(string, substring):
    return(string.find(substring, string.find(substring) + 1))

if __name__=='__main__':
    
    Url = ["https://www.sportsv.net/events/worldcup2018/list"]
    chromeOptions = webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096 }
    chromeOptions.add_experimental_option("prefs", prefs)
    #web = webdriver.Chrome("E:\Walt\Python\chromedriver_win32\chromedriver", chrome_options=chromeOptions)
    web = webdriver.Chrome("/Users/walt/downloads/chromedriver", chrome_options=chromeOptions)
    web.get(Url[0])
    #抓網址
    check = "first"
    while check != "-1":
        Links = web.find_elements_by_xpath('//*[@class="fifa_more_leftbox all-list"]//a')
        for i in Links:
            Link_All.append(i.get_attribute("href"))
        next = web.find_element_by_link_text("下一頁")
        next.click()
        check = web.find_element_by_link_text("下一頁").get_attribute("tabindex")
        print(check)
        time.sleep(3)
    print(Link_All[1])
    '''
    sql = "select website from sports_news_backup"
    cursor.execute(sql)
    old_url = list(cursor)
    Link_All = []
    for i in range(len(old_url)):
       Link_All.append(old_url[i][0])
    print("NO:", len(Link_All))
    '''

    for i in range(len(Link_All)):
        web.get(Link_All[i])
        #web.get("https://www.sportsv.net/articles/53566")
        # 主題
        Title_1 = web.find_element_by_xpath('//*[@class="fifa_container_article"]//*[@class = "title"]/h1')
        # 群組, 作者, 時間
        Title_2 = web.find_element_by_xpath('//*[@class="fifa_container_article"]//*[@class = "title"]/h3[1]')
        fir = Title_2.text.find("|")
        sec = find_2nd(Title_2.text, "|")
        Type = Title_2.text[0:fir]
        Author = Title_2.text[fir+1:sec]
        _Date = Title_2.text[sec+1:len(Title_2.text)]
        # 內文
        Temp_1 = web.find_elements_by_xpath('//*[@class="article_content"]//p//span')
        Temp_2 = web.find_elements_by_xpath('//*[@class="article_content"]//p')
        if len(Temp_1) < len(Temp_2):
            Temp_1 = Temp_2 
        # 組合內文
        Content = []
        for j in Temp_1:
            Content.append(j.text)
        # 塞進 DB
        InsertValue = {"Website": Link_All[i], "Title": Title_1.text, "Type": Type, "Author": Author, "Date": _Date, "Content": ",".join(Content)}
        print(InsertValue)
        Insert_DB(InsertValue)
        time.sleep(3)

    web.close()
    web.quit()

        

