import requests
import pandas as pd 
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime 
import numpy as np

#Initialize variables as preliminaries
url = 'https://web.archive.org/web/20230902185326/https://en.wikipedia.org/wiki/List_of_countries_by_GDP_%28nominal%29'
csv_path = './Countries_by_GDP.csv'
table_attribs = ["Country","GDP_USD_millions"]
db_name = 'World_Econimies.db'
table_name = 'Countries_by_GDP'

##Extraction process

def extract(url, table_attribs):
    page = requests.get(url).text
    data = BeautifulSoup(page,'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    table = data.find_all('tbody')
    rows = table[2].find_all('tr')
    for row in rows:
        col = row.find_all('td')
        if len(col)!=0:
            if col[0].find('a') is not None and '—' not in col[2]:    
                data_dict = {
                    "Country" : col[0].a.contents[0],
                    "GDP_USD_millions" : col[2].contents[0]
                }
                df1 = pd.DataFrame(data_dict, index = [0])
                df = pd.concat([df,df1], ignore_index=True)
                
    return df

##transforming process, we want to pass from millions to billions
def transform(df):
    GDP_list = df["GDP_USD_millions"].tolist()
    GDP_list = [float("".join(x.split(','))) for x in GDP_list]
    GDP_list = [np.round(x/1000,2) for x in GDP_list]
    df["GDP_USD_millions"] = GDP_list
    df=df.rename(columns = {"GDP_USD_millions":"GDP_USD_billions"})
    return df

##loading to a csv file
def load_to_csv(df, csv_path):
    df.to_csv(csv_path)

##loading to database
def load_to_sql(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

##Query automation to show the data from db
def run_query(query_statement, sql_connection):
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)

##logging process
def log_progress(message): 
    timestamp_format = '%Y-%h-%d-%H:%M:%S' # Year-Monthname-Day-Hour-Minute-Second 
    now = datetime.now() # get current timestamp 
    timestamp = now.strftime(timestamp_format) 
    with open("./etl_project_log.txt","a") as f: 
        f.write(timestamp + ' : ' + message + '\n')

##Starting point for the pipeline

##Preliminaries complete
log_progress('Preliminaries complete. Initiating ETL process')

#create df with extract function
df = extract(url, table_attribs)
log_progress('Data extraction complete. Initiating Transformation process')

#transform the data from df that was created before
df = transform(df)
log_progress('Data transformation complete. Initiating loading process')

#loading data to csv and to the db
load_to_csv(df, csv_path)
log_progress('Data saved to CSV file')
sql_connection = sqlite3.connect(db_name)
log_progress('SQL Connection initiated.')
load_to_sql(df, sql_connection, table_name)
log_progress('Data loaded to Database as table. Running the query')

#select table from the db
query_statement = f"SELECT * from {table_name} WHERE GDP_USD_billions >= 100"
run_query(query_statement, sql_connection)
log_progress('Process Complete.')

#close db connection
sql_connection.close()