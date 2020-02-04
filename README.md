# NewsAggregator-2.0
This actions this script performs are as follows:
* From a list of RSS feed URLs in a file, request all the headline data
* Parse the RSS feed XML, and store the data to an SQLite database
* Query the database for the most recent stories from each news source
* Output those newest stories to HTML in a presentable format

The biggest challenge I encountered with this one was trying to come up with a database schema for something as un-structured as RSS feed data. I ultimately decided to use the title and link together as a composite key for each of the 2 tables, with the schema:
    
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

This was the first time I've used python to output an HTML like this. It was a pretty fun function to write!
