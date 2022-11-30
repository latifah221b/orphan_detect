#!/usr/bin/env python
from way.session import Session
from way.pack import Pack
from way.cdx import search
import json
import logging

def read_list(file_name):
    urls = []
    with open(file_name) as f:
        [urls.append(line) for line in f.readlines()]
        return  urls

def store_json(file_name,all_urls):
    with open(file_name, 'w') as fp:
        json.dump(all_urls, fp, sort_keys=True, indent=4)

def read_json(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
    return  data

def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write('\n'.join(urls))

def downloadsnapshots(from_date:int ,to_date:int, url:str,all_urls ):
    args_string = '{ "quiet":false, "progress":false, "user_agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36", ' \
                  '"follow_redirects":true,"max_retries":3, ' \
                  '"url":"%s","from_date":%d,"to_date":%d,"uniques_only":true,' \
                  '"list":true, "raw":true,"root":"https://web.archive.org","ignore_errors":true,"no_clobber":false }'
    s = args_string % (url, from_date, to_date)
    args = json.loads(s,strict=False)

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

    timestamps = [snap["timestamp"] for snap in snapshots]
    last_modified = 0
    if len(timestamps)> 0:
        last_modified = timestamps[len(timestamps)-1]

    if len(timestamps) > 0 and len(timestamps) < 20 and int(last_modified[:4]) > 2016:
       pack = Pack(
           args["url"],
        timestamps=timestamps,
        session=session
       )
       dict = pack.download_to(
        "./",
        raw=args["raw"],
        root=args["root"],
        ignore_errors=args["ignore_errors"],
        no_clobber=args["no_clobber"],
        progress=args["progress"]
       )
       if len(dict) > 0:
           res = list(dict.keys())
           l = dict[res[0]]
           last_modified = res[0]
           for d in res:
               if dict[d] != l:
                   l = dict[d]
                   last_modified = d

    if len(timestamps) > 0:
        dd = {"url": args["url"],"age": timestamps[0][:4] ,
               "last_archived_version": last_modified[:4]}
        all_urls.append(dd)


def main():
    all_urls = []

    urls = read_list("reachable_{}_filtred_across_years.txt".format(2021))
    print()
    i = 1.0
    for u in urls:
        downloadsnapshots(1997,2022,u,all_urls)
        i = i+1.0
        print(i/len(urls))

    store_json("{}_compersion.json".format(2021), all_urls)

if __name__ == "__main__":
    main()
