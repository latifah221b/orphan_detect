#!/usr/bin/env python
import asyncio
from Urlspinging.filter_out404 import  filter_all
import time
def read_list(file_name):
    urls = []
    with open(file_name) as f:
        [urls.append(line) for line in f.readlines()]
        return  urls

def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write("".join(urls))

async def filter_out(year):

    urls = read_list('./reachability_test/reachable_{}.txt'.format(year))
    start = time.time()

    a = await filter_all(urls)
    store_list(a, './error_pages_removing/reachable_{}_filtred.txt'.format(year))

    end = time.time()
    print(f'original links {len(urls)} links in {end - start} seconds')
    print(f'reduced links {len(a)} links in {end - start} seconds')

def main():

    # filter out reachable pages based on black keywords
    # if the innerhtml contains these strings
    #     blackword = "This app has been disabled"
    #     blackword1 = "404 Not Found"
    #     blackword2 = "403 Forbidden"

    year = 1997
    while (year < 2023):
        asyncio.run(filter_out(year))
        year += 2



if __name__ == "__main__":
    main()
