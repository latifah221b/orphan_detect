import asyncio
from Urlspinging.urlsStatus import download_all
import time

def read_list(file_name):
    urls = []
    with open(file_name) as f:
        [urls.append(line) for line in f.readlines()]
        return  urls



def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write(''.join(urls))

async def check_reachability(urls:list):
    start = time.time()
    a = await download_all(urls)
    end = time.time()
    print(f'Reachable links {len(a)} links in {end - start} seconds')
    return a


async def check_rechabbility_of_year(urls:list, year):
    a = await check_reachability(urls)
    store_list(a, './reachability_test/reachable_{}.txt'.format(year))
    print(f'Reachable links {len(a)} for {year}')

def main():
    #check_reachability all pages from 1997 to 2022,each round will cover two years
    year = 1997
    while (year < 2023):
        asyncio.run(check_rechabbility_of_year(read_list("./original_list_after_filtering/urls_{}.txt".format(year)), year))
        year += 2

if __name__ == "__main__":
    asyncio.run(main())
