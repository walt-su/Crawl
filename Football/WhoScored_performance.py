#-*- coding: utf-8 -*-
from selenium import webdriver
import MySQLdb as mysql 
import time
import datetime
import re
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

def Insert_DB(InsertValue):
	placeholders = ', '.join(['%s'] * len(InsertValue))
	columns = ', '.join(InsertValue.keys())
	sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('Soccer_TeamPerformance', columns, placeholders)
	cursor.execute(sql,InsertValue.values())
	conn.commit()

if __name__ == "__main__":

	conn = mysql.connect(user = "", passwd = "", db = "")
	cursor = conn.cursor()

	sql = 'select * from soccer_matchresult a where a.datetime >= (curdate()-INTERVAL 2000 DAY) and a.HomeScore is not NULL and \
	not exists (select url from soccer_teamperformance b where b.datetime >= (curdate()-INTERVAL 2000 DAY) and a.url=b.url)'
	#這裡只爬matchresult有, 但performance裡沒有的URL, 且在matchresult裡的主隊分數都要有, 即沒有延賽。
	cursor.execute(sql)
	MR = list(cursor) # Match Result data
	print("Total", len(MR), "data will be crawled:")

	chromeOptions = webdriver.ChromeOptions()
	prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096 }
	chromeOptions.add_experimental_option("prefs", prefs)

	if (len(MR) != 0):
		web = webdriver.Chrome("E:\Walt\Python\chromedriver_win32\chromedriver", chrome_options=chromeOptions)
		a = datetime.datetime.now()        # To calculate execute time		
		for i in range(len(MR)):
			error_sum = 0
			while True:
				try:
					web.get(MR[i][1])
					time.sleep(3)
					# Match Center data
					MC = [re.split(pattern='\n|-',string=j.text)[0:3] for j in web.find_elements_by_xpath('//*[@id="match-centre-stats"]/ul/li[1]')] +\
						 [re.split(pattern='\n|-',string=j.text)[0:3] for j in web.find_elements_by_xpath('//li[@class="match-centre-stat  has-stats"]') if j.text != '']

					for k in range(len(MC)):
						MC[k][1], MC[k][2] = float(MC[k][1]), float(MC[k][2])

					# Chalk Board data
					web.find_element_by_xpath('//ul[@id = "live-match-options"]/li[3]/a').click() 
					CB = [re.split(pattern='\n|-',string=j.text)[0:3] for j in web.find_elements_by_xpath("//li[@class = 'filterz-option']")]
					for k in range(len(CB)):
						CB[k][1], CB[k][2] = float(CB[k][1]), float(CB[k][2])

					# ForMation data
					FM = [j.text for j in web.find_elements_by_xpath('//div[@class = "formation"]') if j.text != ""]

					# Final result
					FTR = ""
					score = float(MR[i][6]) - float(MR[i][7])
					if score > 0:
						FTR = "H"
					elif score == 0:
						FTR = "D"
					else:
						FTR = "A"

					Insert_data = {'URL':MR[i][1], 'TYPE': MR[i][2], 'DATETIME':  MR[i][3], 'HOMETEAM': MR[i][4], 'AWAYTEAM': MR[i][5],	'HOMESCORE': MR[i][6], 'AWAYSCORE': MR[i][7],\
					               'H_RATINGS': MC[0][1], 'H_TOTALSHOTS': MC[1][1], 'H_POSSESSION': MC[2][1], 'H_PASSSUCCESSRATE': MC[3][1], 'H_DRIBBLES': MC[4][1], 'H_AERIALSWON': MC[5][1],\
					               'H_TACKLES': MC[6][1], 'H_CORNERS': MC[7][1], 'H_DISPOSSESSED': MC[8][1], 'H_PASSES': CB[1][1], 'H_TOTALDRIBBLES': CB[2][1], 'H_TOTALTACKLES': CB[3][1],\
					               'H_INTERCEPTIONS': CB[4][1], 'H_CLEARANCES': CB[5][1], 'H_BLOCKS': CB[6][1], 'H_OFFSIDES': CB[7][1], 'H_FOULS': CB[8][1], 'H_AERIALDUELS': CB[9][1],\
					               'H_TOUCHES': CB[10][1], 'H_LOSSPOSSESSION': CB[11][1], 'H_ERRORS': CB[12][1], 'H_SAVES': CB[13][1], 'H_CLAIMS': CB[14][1], 'H_PUNCHES': CB[15][1], 'H_FORM': FM[0],\
					               'A_RATINGS': MC[0][2], 'A_TOTALSHOTS': MC[1][2], 'A_POSSESSION': MC[2][2], 'A_PASSSUCCESSRATE': MC[3][2], 'A_DRIBBLES': MC[4][2], 'A_AERIALSWON': MC[5][2],\
					               'A_TACKLES': MC[6][2], 'A_CORNERS': MC[7][2], 'A_DISPOSSESSED': MC[8][2], 'A_PASSES': CB[1][2], 'A_TOTALDRIBBLES': CB[2][2], 'A_TOTALTACKLES': CB[3][2],\
					               'A_INTERCEPTIONS': CB[4][2], 'A_CLEARANCES': CB[5][2], 'A_BLOCKS': CB[6][2], 'A_OFFSIDES': CB[7][2], 'A_FOULS': CB[8][2], 'A_AERIALDUELS': CB[9][2],\
					               'A_TOUCHES': CB[10][2], 'A_LOSSPOSSESSION': CB[11][2], 'A_ERRORS': CB[12][2], 'A_SAVES': CB[13][2], 'A_CLAIMS': CB[14][2], 'A_PUNCHES': CB[15][2], 'A_FORM': FM[1],\
					               'WL': score,	'FTR': FTR}
					#print (Insert_data)
					Insert_DB(Insert_data)
					print ("Insert", "No."+str(i+1), ":", MR[i][1], MR[i][3], MR[i][2], " -> OK")
				except Exception as e:
					print ("Insert", "No."+str(i+1), ":", MR[i][1], MR[i][3], MR[i][2], " -> Fail")
					print ("Error11", e)
					error_sum += 1
					if error_sum > 3:
						web.close()
						web.quit()
						web = webdriver.Chrome("E:\Walt\Python\chromedriver_win32\chromedriver", chrome_options=chromeOptions)
						print("Re-open a window.")
				else:
					break
		web.close()
		web.quit()
		b = datetime.datetime.now()
		print ("Total time: ", (b-a))
	else:
		print ("There is no new data in soccer_matchresult.")

	sql = "delete from Soccer_TeamPerformance where rowid not in (select * from (select max(rowid) from Soccer_TeamPerformance group by TYPE,DATETIME,HOMETEAM,AWAYTEAM,HOMESCORE,AWAYSCORE,H_RATINGS) as t)"
	#sql = "delete from Soccer_TeamPerformance where rowid not in (select max(rowid) from Soccer_TeamPerformance group by TYPE,DATETIME,HOMETEAM,AWAYTEAM,HOMESCORE,AWAYSCORE,H_RATINGS)"
	cursor.execute(sql)

	conn.commit()
	conn.close()


