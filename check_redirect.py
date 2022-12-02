import asyncio
from Urlspinging.check_for_redirect_urls import download_all
import re
import json

def store_json(file_name,all_urls):
    with open(file_name, 'w') as fp:
        json.dump(all_urls, fp, sort_keys=True, indent=4)

def read_json(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
    return  data

def main():
    #check_redirect all pages from 1997 to 2022,each round will cover two years
    year = 1997
    while year < 2019:
        json = read_json("./potential_orphaned_urls/{}_potential_orphaned.json".format(year))
        a = asyncio.run(download_all(json))
        store_json('./redirect_test/noneredirect_{}.json'.format(year), a)
        print(f'none redirect links {len(a)} for {year}')
        year += 2


if __name__ == "__main__":
   main()