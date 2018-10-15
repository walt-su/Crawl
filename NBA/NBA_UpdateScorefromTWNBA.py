# -*- coding: utf-8 -*-
import urllib.request as ur
from urllib.error import URLError, HTTPError
import json
from pprint import pprint
import datetime
import MySQLdb as mariadb 
import time

conn = mariadb.connect(user="", passwd="", db="", charset="utf8")
cursor = conn.cursor()

def UpdateDB(InsertValue):
	sql = "update NBA_Game set HomeScore = %s, AwayScore = %s where HomeTeam = %s and AwayTeam = %s and Date = %s"
	cursor.execute(sql, InsertValue)
	conn.commit()
	print("Updated successfully!")


if __name__=='__main__':
     
	mon_day = []
	for d in range(0, 7):
		mon_day.append([
			str(datetime.datetime.now() - datetime.timedelta(days=d))[0:4],
			str(datetime.datetime.now() - datetime.timedelta(days=d))[5:7], 
			str(datetime.datetime.now() - datetime.timedelta(days=d))[8:10]])

	header = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
		}

	for i in mon_day:
		url = "https://tw.global.nba.com/stats2/season/schedule.json?countryCode=TW&gameDate="+i[0]+"-"+i[1]+"-"+i[2]+"&locale=zh_TW&tz=%2B8"
		#url = "https://tw.global.nba.com/stats2/season/schedule.json?countryCode=TW&gameDate=2018-01-01&locale=zh_TW&tz=%2B8"
		print("Date:", i[0]+"/"+i[1]+"/"+i[2])
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
				InsertValue = [HomeScore, 
			        	       AwayScore,
							   HomeTeam, 
					           AwayTeam, 
			    	           datetime.datetime.strptime(Date, "%a %b %d %H:%M:%S %Y")]
				UpdateDB(InsertValue)

		except IndexError as err:
			print("No game!")
		except HTTPError as err:
			print("HTTPError:", err.code)
		except URLError as err:
			print("URLError")

		time.sleep(1)




	