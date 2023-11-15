""" 
TODO:
    make stat recorder using heirickdev (for in depth team analysis)
    add data is not finished
    
"""

import json
import requests
import os
from time import sleep
from random import random
from bs4 import BeautifulSoup
import sqlite3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType

REGIONS = ["NA_US_WEST", "NA_US_EAST", "EU_WEST", "EU_CENTRAL_EAST", "EU_MIDDLE_EAST", "EU_TURKEY", "AP_ASIA", "AP_JAPAN", "AP_OCEANIA", "AP_SOUTH_ASIA", "KR_KOREA", "LATAM_NORTH", "LATAM_SOUTH", "BR_BRAZIL"]
#REGIONS = ["NA_US_WEST"]
DIVS = [20, 19, 18, 17]
DIR = "tracker"
VERBOSE = True

class Scraper:

    def __init__(self, headless=True):

        self.proxies = []
        self.driver = None
        self.proxy_index = -1

        self.options = Options() 
        if headless:
            self.options.add_argument("-headless") 
        self.options.set_preference('devtools.jsonview.enabled', False)
        self.load_proxies()
        self.update_proxy()
        self.driver.set_page_load_timeout(30)

    def find_element(self, by, param):
        return self.driver.find_element(by, param)
    
    def get(self, url):
        self.driver.get(url)
    
    def load_proxies(self, path="proxies.json"):
        str_proxies = json.load(open(path, "r"))
        for proxy in str_proxies:
            self.proxies.append(Proxy({"proxyType": ProxyType.MANUAL, "httpProxy": proxy,"ftpProxy": proxy, "sslProxy": proxy}))

    def update_proxy(self):
        self.proxy_index += 1
        if self.driver != None:
            self.driver.quit()
        self.driver = webdriver.Firefox(options=self.options, proxy=self.proxies[self.proxy_index])

    def quit(self):
        self.driver.quit()


def info(s):
    if VERBOSE:
        print(s)

def scrape_team_ids(region, div):
    team_ids = []
    page = 1
    page_lim = 3
    while page <= page_lim:
        url = "http://tracker.gg/valorant/premier/standings?region={reg}&division={div}&page={page}".format(reg=region, div=div,page=page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        elems = []
        while len(elems) <= 0:
            elems = soup.find_all("div", "roster flex flex-col")
            if len(elems) > 0:
                for elem in soup.find_all("div", "roster flex flex-col"):
                    team_ids.append(elem["data-roster"])
            else:
                print("bot error waiting")
                sleep(300)

        page_lim = int(soup.find_all("a", "router-link-active number")[-1].text)
        page += 1

        info("found {} team ids in total".format(len(team_ids)))
    
    return team_ids

def scrape_match_ids(driver, team_ids):
    match_ids = []
    for id in team_ids:
        while True:
            try:
                driver.get("https://api.tracker.gg/api/v1/valorant/premier/roster/{id}/summary".format(id=id))
                for match in json.loads(driver.find_element(By.XPATH, "//*").text)["data"]["recentMatches"]:
                    id = match["matchId"]
                    if not id in match_ids:
                        match_ids.append(id)
                break
            except:
                info("error in scrape_match_ids, changing proxy" + driver.find_element(By.XPATH, "//*").text)
                driver.update_proxy()

        info("found {} match ids in total".format(len(match_ids)))
    
    return match_ids

def scrape_match(driver, id):
    while True:
        try:
            driver.get("https://api.tracker.gg/api/v2/valorant/standard/matches/{id}".format(id=id))
            return json.loads(driver.find_element(By.XPATH, "//*").text)["data"]
        except:
            info("error in scrape_match, changing proxy" + driver.find_element(By.XPATH, "//*").text)
            driver.update_proxy()

def scrape_matches(driver, match_ids):
    matches = []
    for id in match_ids:
        matches.append(scrape_match(driver, id))
    return matches

""" returns a 3 tuple of data containing the team ids, match ids, and matches for a given region and division """
def get_files(reg_dir, div_dir, team_ids_fname="team_ids.json", match_ids_fname="match_ids.json", matches_dir="matches", dir=DIR):
    
    path = os.path.join(os.path.join(os.path.join(os.getcwd(), dir), reg_dir), div_dir)
    
    team_ids = []
    team_ids_path = os.path.join(path, team_ids_fname)
    if os.path.exists(team_ids_path): # if the path does not exist, move onto the next one
        with open(team_ids_path) as team_ids_file:
            team_ids = json.load(team_ids_file)
        
    match_ids = []
    match_ids_path = os.path.join(path, match_ids_fname)
    if os.path.exists(match_ids_path):
        with open(match_ids_path) as match_ids_file:
            match_ids = json.load(match_ids_file)
        
    matches = {}
    matches_path = os.path.join(path, matches_dir)
    if os.path.exists(matches_path):
        for match_fname in os.listdir(matches_path):
            match_path = os.path.join(matches_path, match_fname)
            if os.path.exists(match_path):
                with open(match_path) as match_file:
                    matches[match_fname[:-5]] = json.load(match_file)

    return team_ids, match_ids, matches

""" returns a data dict sepparated into regions, division, and then team ids, match ids, and matches """
def load_data(dir=DIR):

    data = {}

    for region in REGIONS:
        data[region] = {}

        for div in DIVS:

            team_ids, match_ids, matches = get_files(region, str(div), dir=dir)

            data[region][div] = {"team_ids": team_ids, 
                                "match_ids": match_ids, 
                                "matches": matches} 
            
    return data

def write_json(data, fname, dir=DIR):
    path = os.path.join(os.getcwd(), dir)
    try:
        os.makedirs(path)
        info("created files to " + path)
    except:
        pass
    finally:
        loc = os.path.join(path, fname)
        with open(loc, "w") as file:
            json.dump(data, file)
            info("dumped data to " + loc)

data = load_data()
driver = Scraper(headless=True)

for region in REGIONS:
    reg_dir = os.path.join(DIR, region)
    for div in DIVS:
            dir = os.path.join(reg_dir, str(div))

            print("scraping team ids for division {div} in {region}".format(region=region, div=div))
            if data[region][div]["team_ids"] == []: # if there is already data for this region/ division, do not scrape
                data[region][div]["team_ids"] = scrape_team_ids(region, div)
                print("{} total team ids scraped".format(len(data[region][div]["team_ids"])))
                write_json(data[region][div]["team_ids"], "team_ids.json", dir=dir)
            else:
                print("{} total team ids found on disk, no scraping required".format(len(data[region][div]["team_ids"])))

            print("scraping match ids for division {div} in {region}".format(region=region, div=div))
            if data[region][div]["match_ids"] == []: # if there is already data for this region/ division, do not scrape
                data[region][div]["match_ids"] = scrape_match_ids(driver, data[region][div]["team_ids"])
                print("{} total match ids scraped".format(len(data[region][div]["match_ids"])))
                write_json(data[region][div]["match_ids"], "match_ids.json", dir=dir)
            else:
                print("{} total match ids found on disk, no scraping required".format(len(data[region][div]["match_ids"])))

            print("scraping matches for division {div} in {region}".format(region=region, div=div))
            for id in data[region][div]["match_ids"]:
                if not (id in data[region][div]["matches"]):
                    match = scrape_match(driver, id)
                    data[region][div]["matches"][id] = (match)
                    print("{} total matches scraped".format(len(data[region][div]["matches"])))
                    write_json(match, id + ".json", dir=os.path.join(dir, "matches"))
                    #sleep(20) # timeout is likely 1 hour or 1 day, rate limit is likely 100 requests/30 mins
                else:
                    print("match {} found on disk, no scraping required".format(id))
                    print("{} total matches scraped".format(len(data[region][div]["matches"])))

#write_json(data, "data.json")

driver.quit()
