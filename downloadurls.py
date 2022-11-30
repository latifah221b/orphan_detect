#!/usr/bin/env python
import asyncio
from way.session import Session
from way.cdx import search
from Urlspinging.urlsStatus import download_all
from Urlspinging.urlsStatus import http_normalize_slashes
import json
import logging
import time


def downloadsnapshots(from_date:int ,to_date:int ):
    args_string = '{ "quiet":false, "progress":true, "user_agent":"waybackpack", ' \
                  '"follow_redirects":true,"max_retries":0, ' \
                  '"url":"http://cs.brown.edu*","from_date": %d,"to_date": %d,"uniques_only":true,' \
                  '"list":true, "raw":true,"root":"https://web.archive.org","ignore_errors":true,"no_clobber":false   }'
    s = args_string % (from_date, to_date)

    args = json.loads(s)

    logging.basicConfig(
        level=(logging.WARN if (args["quiet"] or args["progress"]) else logging.INFO),
        format="%(levelname)s:%(name)s: %(message)s"
    )
    session = Session(
        user_agent=args["user_agent"],
        follow_redirects=args["follow_redirects"],
        max_retries=args["max_retries"]
    )
    snapshots = search(args["url"],
                       session=session,
                       from_date=args["from_date"],
                       to_date=args["to_date"],
                       uniques_only=args["uniques_only"],
                       )
    return snapshots

def filter_out_none_html(snapshots):
    keyValList = ['text/html']
    filtered_list = [d for d in snapshots if d['mimetype'] in keyValList]

    return filtered_list

def filter_out_duplicates_urls(filtered_list):
    urls = []
    for x in filtered_list:
        a = http_normalize_slashes(x["original"])
        if a not in urls:
            urls.append(a)
    return urls


def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write('\n'.join(urls))

def check_reachability(urls:list):
    start = time.time()
    a = asyncio.run(download_all(urls))
    end = time.time()
    print(f'download {len(urls)} links in {end - start} seconds')
    print(f'Reachable links {len(a)} links in {end - start} seconds')

    return a

async def download_filter_snapchats(from_date,to_date):

    snapshots = downloadsnapshots(from_date,to_date)
    print("Original List from {} to {}: ".format(from_date,to_date), len(snapshots))
    filtered_list = filter_out_none_html(snapshots)
    print("The List from {} to {} After filtering out non-html: ".format(from_date,to_date), len(filtered_list))

    urls = filter_out_duplicates_urls(filtered_list)
    print("The List from {} to {} After removing duplicates: ".format(from_date,to_date), len(urls))
    store_list(urls, "urls_{}.txt".format(from_date))

    a = check_reachability(urls)
    store_list(a, 'reachable_{}.txt'.format(from_date))

async def downloadyears():
    year = 1997
    tasks = []
    while(year< 2023):
      task = asyncio.ensure_future(download_filter_snapchats(year, year+1))
      tasks.append(task)
      year += 2
    await asyncio.gather(*tasks, return_exceptions=True)

def main():
    #download all pages from 1997 to 2022,each round will cover two years
    asyncio.run(downloadyears())








if __name__ == "__main__":
    main()
