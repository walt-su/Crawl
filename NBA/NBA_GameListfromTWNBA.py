# -*- coding: utf-8 -*-
import urllib.request as ur
from urllib.error import URLError, HTTPError
import json
from pprint import pprint
import datetime
import MySQLdb as mariadb 
import time
from bs4 import BeautifulSoup

conn = mariadb.connect(user="root", passwd="1111", db="nba", charset="utf8")
cursor = conn.cursor()

def InsertDB(InsertValue):
	placeholder = ",".join(["%s"] * len(InsertValue))
	columns = ",".join(InsertValue.keys())
	sql = "insert into %s (%s) values (%s)" % ("NBA_Game", columns, placeholder)
	cursor.execute(sql, InsertValue.values())
	conn.commit()
	print("Insert successfully!")


if __name__=='__main__':
	year = ["2018", "2019"]
	mon = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
	day = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
	       "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24",
	       "25", "26", "27", "28", "29", "30", "31"]
	#mon = ["02", "03"]	
	     
	header = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
		}

	for i in year:
		for j in mon:
			for k in day:
				url = "https://tw.global.nba.com/stats2/season/schedule.json?countryCode=TW&gameDate="+i+"-"+j+"-"+k+"&locale=zh_TW&tz=%2B8"
				#print(url)
				#url = "https://tw.global.nba.com/stats2/season/schedule.json?countryCode=TW&gameDate=2018-10-09&locale=zh_TW&tz=%2B8"
				print("Date:", i+"/"+j+"/"+k)
				try:
					request = ur.Request(url, headers = header)
					_json = ur.urlopen(request).read()
					load_json = json.loads(_json)
					data = load_json["payload"]["dates"][0]["games"]
					for game in data:
						AwayTeam = game["awayTeam"]["profile"]["city"]+game["awayTeam"]["profile"]["name"]
						HomeTeam = game["homeTeam"]["profile"]["city"]+game["homeTeam"]["profile"]["name"]
						Venue = game["profile"]["arenaName"]
						Date = time.ctime(int(game["profile"]["utcMillis"])/1000)
						AwayScore = game["boxscore"]["awayScore"]
						HomeScore = game["boxscore"]["homeScore"]
						#pprint([AwayTeam, HomeTeam, Venue, Date, AwayScore, HomeScore])
						InsertValue = {"HomeTeam": HomeTeam, 
							           "AwayTeam": AwayTeam, 
					    	           "Venue": Venue,
					    	           "Date": datetime.datetime.strptime(Date, "%a %b %d %H:%M:%S %Y"),
					        	       "HomeScore": HomeScore, 
					        	       "AwayScore": AwayScore}				    
						#print(InsertValue)
						InsertDB(InsertValue)

				except IndexError as err:
					print("No game!")
				except HTTPError as err:
					print("HTTPError:", err.code)
				except URLError as err:
					print("URLError")

				time.sleep(1)
		sql = "delete from NBA_Game where rowid not in (select * from (select max(rowid) from NBA_Game group by HomeTeam,AwayTeam,Venue,Date,HomeScore,AwayScore ) as t)"
		cursor.execute(sql)
		print ("Removal already.")



	