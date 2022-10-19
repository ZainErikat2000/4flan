from array import array
from distutils.command import check
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import re
import concurrent.futures
import time
import os
import asyncio

def getCatalogSource(board: str,isHeadless: bool)->str:
    if(board == None or isHeadless == None):
        print('please choose a board and specify if webdriver should be headless or not')
    if(isHeadless):
        print('headless firefox chosen')
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
    else:
        print('firefox will open shortly')
        driver = webdriver.Firefox()
    print("getting source page")
    driver.get("https://boards.4channel.org"+board+"/catalog")
    html = driver.page_source
    driver.close()
    return html

def getThreadIDs(html: str,board: str)-> array:
    soup = BeautifulSoup(html,'html.parser')

    divs = soup.find_all("div",attrs={'class':'thread'})

    threadURLs = []
    for t in divs:
        id = t.get('id').split('-')[-1]
        url = "https://boards.4channel.org"+board+"thread/"+str(id)
        threadURLs.append(url)

    threadURLs.pop(0)

    return threadURLs

def indexBlockQuotes(threadURL: str,)->array:
    splitURL = threadURL.split('/')
    threadID = splitURL[-1]
    board = splitURL[-3]
    print('Board: '+str(board)+"\nThread: "+str(threadID))
    r = requests.get(threadURL,stream=True)
    posts = []
    if(r.status_code == 200):
        soup = BeautifulSoup(r.text,'html.parser')
        containers = soup.find_all("div",attrs={"class":"postContainer"})
        for cont in containers:
            info = cont.find("div",{'class':'postInfo'})
            postID = str(info.find('a',{'title':'Link to this post'}).get('href'))[2:]
            postDate = info.find('span',{'class':'dateTime'}).get_text()
            posterName = info.find('span',{"class":"name"}).get_text()
            block = cont.find("blockquote")
            quotedPosts = block.find_all("a",{'class':'quotelink'})
            quotedIDs = []
            for qp in quotedPosts:
                quotedIDs.append(qp.get('href')[2:])
            rawPostText = block.get_text()
            filteredPostText = re.sub('(>>)[0-9]*','',rawPostText)
            if(filteredPostText != ''):
                finalPost = {"board": board,
                "thread":threadID,
                "postID" :postID,
                "poster_name":posterName,
                "postDate":postDate,
                "quoted_posts":quotedIDs,
                "raw_text":filteredPostText,}
                posts.append(finalPost)
    return posts

st = time.time()

html = getCatalogSource(board='/pol/', isHeadless=True)
ids = getThreadIDs(html = html,board='/pol/')

import json
import datetime
filename = '/'+str(datetime.datetime.now().strftime("%I-%M-%p_%B-%d-%Y"))+'.json'

catalogPosts = []
with concurrent.futures.ThreadPoolExecutor(50) as exec:
    catalogPosts = list(exec.map(indexBlockQuotes,ids))
i = 0

jObj = []
for x in catalogPosts:
    for y in x:
        jObj.append(y)

with open(filename,'w') as file:
    json.dump(jObj,file,indent=7)

seconds = time.time() - st
print('catalogGetter took '+str(seconds)+' seconds')