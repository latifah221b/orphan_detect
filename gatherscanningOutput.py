import json
import os

def store_json(file_name,all_urls):
    with open(file_name, 'a') as fp:
        json.dump(all_urls, fp, sort_keys=True, indent=4)

def read_json(file_name):
    with open(file_name, 'r') as f:
        if os.path.getsize(file_name)>0:
            data = json.load(f)
            return data
    return None

def read_list(file_name):
    urls = []
    with open(file_name) as f:
        [urls.append(line) for line in f.readlines()]
        return  urls


def main():
    year = 1997
    nn = 0
    nn1 = 0
    nn2 = 0
    d = dict()
    while (year < 2023):
        new_urls = []
        u = read_list(f'./tobeScanned_urls/{year}.txt')

        #print("the {} length: {}".format(year,len(u)))
        n = 1

        while (n <= len(u)):
            urls = read_json(f'./scan_output/{year}/{n}')

            if urls is not None:

                   for v in urls["vulnerabilities"]["SQL Injection"]:
                         print(v['info'])
                         #if v['info']==  "X-Frame-Options is not set":
                         nn = nn+1
                         #if v['info'] == "X-Content-Type-Options is not set":
                                 #nn1 =  nn1+1
                         #if v['info'] == "Strict-Transport-Security is not set":
                                 #nn2 = nn2+1

                        #new_urls.append(u)
            n = n+1
            #d["CSP is not set"] = nn
            #d["X-Frame-Options is not set"] = nn
            #d["X-Content-Type-Options is not set"] = nn1
            #d["Strict-Transport-Security is not set"] = nn2
            #d["HttpOnly flag is not set in the cookie"] = nn
            #d["Secure flag is not set in the cookie"] = nn
            d["SQL Injection via injection in the parameter cid"] = nn


        #print("the list {} length is {}".format(year,len(new_urls)))
        year += 2
    store_json("scanResult/scan", d);


if __name__ == "__main__":
    main()