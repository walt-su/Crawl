# -*- coding: utf-8 -*-
import urllib.request as ur
from urllib.error import URLError, HTTPError
import json
from pprint import pprint
import datetime
#import mysqlclient as mariadb 
import time
import sys

#conn = mariadb.connect(user="root", passwd="1111", db="mlb", charset="utf8")
#cursor = conn.cursor()


print(sys.version)
def InsertDB(InsertValue):
	placeholder = ",".join(["%s"] * len(InsertValue))
	columns = ",".join(InsertValue.keys())
	sql = "insert into %s (%s) values (%s)" % ("MLB_2018_Game", columns, placeholder)
	cursor.execute(sql, InsertValue.values())
	conn.commit()
	print("Insert successfully!")

if __name__=='__main__':
	mon = ["02", "03", "04", "05", "06", "07", "08", "09", "10"]
	day = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
			"13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24",
			"25", "26", "27", "28", "29", "30", "31"]
	
	header = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
		}

	for k in range(len(mon)):
		for j in range(len(day)):
			url = "https://gd.mlb.com/components/game/mlb/year_2018/month_" + mon[k] + "/day_" + day[j] + "/master_scoreboard.json"
			#url = "https://gd.mlb.com/components/game/mlb/year_2018/month_07/day_22/master_scoreboard.json"
			print("Date:", mon[k]+"/"+day[j])
			try:
				#print("test 1", url)
				request = ur.Request(url, headers = header)
				#print("test 2", request)
				_json = ur.urlopen(request).read()
				#print("test 3", _json)
				load_json = json.loads(_json)
				data = load_json["data"]["games"]["game"]
				pprint(data)
				for i in range(len(data)):
					homeScore = 0
					awayScore = 0
					if (data[i].get("linescore") is None) or (data[i]["linescore"].get("inning") is None): 
						homeScore = "-"                                   # 沒有 "linescore" or "inning" 代表還沒有比分, 暫用"-"取代
						awayScore = "-"
					else:
						score = data[i]["linescore"]["inning"]            # 第i場比賽的所有比分
						for l in range(len(score)):                       # 讀取每局的比分
							if score[l]["home"] == "":                    # 最後一局的若沒比分，代表0分
								score[l]["home"] = 0
							if score[l]["away"] == "":
								score[l]["away"] = 0
							homeScore = homeScore + int(score[l]["home"])
							awayScore = awayScore + int(score[l]["away"]) # 累積每局的比分
					InsertValue = {"HomeTeam": data[i]["home_team_name"], 
								   "HomeLoca": data[i]["home_team_city"], 
				    	           "AwayTeam": data[i]["away_team_name"], 
				    	           "AwayLoca": data[i]["away_team_city"], 
				        	       "Date": datetime.datetime.strptime(data[i]["time_date"], "%Y/%m/%d %H:%M") + datetime.timedelta(days=1), #Json的日期比台灣時間少一天
				        	       "Venue": data[i]["venue"], 
				        	       "HomeScore": str(homeScore), 
				        	       "AwayScore": str(awayScore)}
					#print(InsertValue)
					InsertDB(InsertValue)
			except KeyError as err:
				print("No game!")
			except HTTPError as err:
				print("HTTPError:", err.code)
			#except URLError as err:
			#	print("URLError")

			time.sleep(1)





#file = urllib.request.urlopen('https://blog.csdn.net/fengxinlinux/article/details/77281253')
#data = file.read()
#data_str = data.decode("utf-8")
#print(data_str)
'''
url = 'https://www.foxsports.com.tw/baseball/mlb/%E8%B3%BD%E7%A8%8B/'
header = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
	}
request=urllib.request.Request(url, headers=header)
data = ur.urlopen(request).read()

#print(response.decode("utf-8"))



fhandle = open("./1.html", "wb")
fhandle.write(data)
fhandle.close()
'''




	