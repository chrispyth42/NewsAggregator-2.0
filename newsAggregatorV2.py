#!/usr/bin/python3.6
#Getting and parsing the data
import lxml.etree as et
import requests

#Writing to database
import sqlite3
import re

#For getting the current time
import datetime

#Settings variables
storyLimit = 10                 #Amount of most recent news stories to display per source
inFile = 'csfeeds.txt'          #Input text file of RSS feed URLs (1 url per line)
dbFile = 'feedDatabase.sqlite'  #Output database file for news data
siteFile = 'site/index.html'    #Output html file to output data to

#Initialize the database and its tables if they don't exist
db = sqlite3.connect(dbFile)
c = db.cursor()

#Database schema
c.execute("""
    CREATE TABLE IF NOT EXISTS Sources(
        title Varchar(200),
        link Varchar(400),
        description Varchar (1000),
        pubDate Varchar(40),
        language Varchar(50),
        docs Varchar(100),
        webMaster Varchar(100),
        PRIMARY KEY (title,link)
        )
""")
c.execute("""
    CREATE TABLE IF NOT EXISTS Articles(
        link Varchar(400),
        title Varchar(200),
        description Varchar(1000),
        pubdate Varchar(40),
        guid Varchar(400),
        category Varchar(500),
        source Varchar(200),
        getDate Date,
        PRIMARY KEY (link,title)
    )
""")

#Current date/time
x = datetime.datetime.now()
datestring = f"{x.year}-{x.month}-{x.day} {x.hour}:{x.minute}:{x.second}"


#Retrieves an RSS feed from a URL, and returns: (meta(dict), content(list of dicts))
#meta contains information about the RSS feed itself, while the content dicts contain different items of the RSS feed
#-----------------------------------------------------------------------------------------------------------------------
#Regex removes HTML tags, special html characters, newlines, tabs, single quotes, and backslashes from the incoming text
# r"<[^>]+>|&[^;]+;|\n|\t|'|\\"
def rssGet(url):
    #Get the document
    r = requests.get(url.strip())

    #Return variables
    meta = dict()       #Metadata of the RSS feed itself
    content = list()    #Story items within the RSS feed

    #If the request was successful, get the data
    if r.ok:
        #Parse the XML, and exit with null if there were errors
        try:
            data = et.fromstring(r.content)
        except:
            print(f'{url.strip()} : Returned broken XML')
            return None
        
        rss = data.findall('.//channel') 
        #Iterate through every document in the rss feed (should be only 1)
        for document in rss:
            #Iterate through every tag in the document
            for thing in document:
                #If it's not under an item tag (indicating it's metadata), add it to the meta dictionary
                if thing.tag != "item":
                    if thing.text:
                        meta[thing.tag] = re.sub(r"<[^>]+>|&[^;]+;|\n|\t|\'|\\",'',thing.text)
                    else:
                        meta[thing.tag] = ''
                #If it is an item tag, iterate through that and append it to the content list as a dictionary
                else:
                    story = dict()
                    for headline in thing:
                        if headline.text:
                            story[headline.tag] = re.sub(r"<[^>]+>|&[^;]+;|\n|\t|\'|\\",'',headline.text)
                        else:
                            story[headline.tag] = ''
                    content.append(story)

    #Return null if the request was unsuccessful
    else:
        print(f"{url.strip()} : Request failed with the status code: {r.status_code}")
        return None

    #Return the data
    return (meta,content)

#One hell of a messy print block that outputs the results of rssFeedRetriever() for debug and viewing purposes
def printRss(results):
    if results:
        print("Metadata")
        print("-"*30)
        for tag in results[0]:
            print(f"{tag}: {results[0][tag]}")
        print("-"*30)
        print("Stories")
        print("-"*30)
        for story in results[1]:
            for tag in story:
                print(f"{tag}: {story[tag]}")
            print("\n")
        print("-"*30)

#A lighter print function that just prints metadata, and the story titles
def printRssLite(results):
    if results:
        print()
        print("#"*20)
        for i in results[0]:
            print(f"{i}: {results[0][i]}")
        print("-"*20)
        for i in results[1]:
            print(i['title'])

#Exports feed information to an sqlite database
def writeFeed(data):
    if data:
        #Schema of database tables, which specify tags to lift from RSS feed data
        Source = ["title","link","description","pubDate","language","docs","webMaster"]
        Article = ["link","title","description","pubDate","guid","category"]

        #Check to see if the source is already in the database
        c.execute(f"SELECT title FROM Sources WHERE title='{data[0]['title']}' AND link='{data[0]['link']}'")
        
        #If it's not, instert a new entry for it from the metadata part of the dictionary
        if not c.fetchall():
            sQuery = "INSERT INTO Sources VALUES ("
            for tag in Source:
                if tag in data[0]:
                    if data[0][tag]:
                        sQuery += (f"'{data[0][tag]}',")
                    else:
                        sQuery += 'NULL,'
                else:
                    sQuery += 'NULL,'
            sQuery = sQuery[:-1] + ")"
            c.execute(sQuery)
        

        #Count of new articles added
        newArticles = 0
        for story in data[1]:
            #Check if article is already in the database
            c.execute(f"SELECT link FROM Articles WHERE title='{story['title']}' AND link='{story['link']}'")
            
            #If not, add it in
            if not c.fetchall():
                newArticles += 1
                aQuery = "INSERT INTO Articles VALUES ("
                for tag in Article:
                    if tag in story:
                        if story[tag]:
                            aQuery += (f"'{story[tag]}',")
                        else:
                            aQuery += "NULL,"    
                    else:
                        aQuery += "NULL,"

                #Add station name and current datetime to the query
                aQuery += f"'{data[0]['title']}', '{datestring}')"
                c.execute(aQuery)
        
        #Print statement for each news source
        print(f"{data[0]['title']}: +{newArticles}")

#Reads from the database, and outputs to an HTML to be used on the webpage
def writeSite():

    #HTML document, starting with the header
    document = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <link rel="stylesheet" href="style.css">
        <title>Chris News</title>
    </head>
    <body>
        <div class="main">
            <br>
            <h1>News Headlines</h1>"""

    #Get all source names
    c.execute("SELECT title FROM Sources")
    sources = c.fetchall()

    #For every source name, query for the news stories
    for res in sources:
        source = res[0]
    
        #Add beginning of source div
        document += f"""
            <div class="station">
            <a href="#" onclick="return togglePageElementVisibility('station-{source}')"><h2>{source}</h2></a>
            <div id="station-{source}" style="display: none">
            """
    
        #Get most recent stories for the source
        c.execute(f"""
            SELECT title,getDate,description,link FROM Articles 
            WHERE source='{source}' 
            ORDER BY getDate DESC
            LIMIT {storyLimit}""")
        stories = c.fetchall()

        #Add to the document for each story
        for story in stories:
            document += f"""
            <div class="story">
                <h3>{story[0]}</h3>
                <p>{story[1]}</p>
                <p>{story[2]}</p>
                <a href="{story[3]}">Link to story</a>
            </div>"""

        #Close the news source div and add a page break
        document += "</div></div><br>"

    #Close the body
    document += "</div></body>"
    
    #Include script reference
    document += """
    <script src="showhide.js"></script>
    </html>"""

    #Write the completed document
    fp = open(siteFile,'w')
    fp.write(document)
    fp.close()

#Main function
def main():
    #Open RSS feed input file
    sources = open(inFile,'r')

    #For each URL, get the RSS data and add it to the database
    for source in sources:
        source = source.strip()
        #Skip lines that are only whitespace
        if source:
            data = rssGet(source)
            writeFeed(data)
    
    #Close input file
    sources.close()

    #Read the database, and output the news stories in an easy to read HTML format
    writeSite()

#Run main function, then save and close the DB
main()
db.commit()
db.close()

