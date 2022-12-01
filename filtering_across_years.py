#!/usr/bin/env python

def normalize_url(url):
    url = url.replace("http://www.", "")
    url = url.replace(":80","")
    url = url.replace("http://","")
    url = url.replace("https://","")
    return url

def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write(''.join(urls))

def read_list(file_name):
    urls = []
    with open(file_name) as f:
        [urls.append(line) for line in f.readlines()]
        return  urls


def filterout():
    year = 1997
    all_urls = set()
    while (year < 2023):
        new_urls = []
        urls = read_list("reachable_{}_filtred_normalized.txt".format(year))
        for u in urls:
            if u not in all_urls:
                new_urls.append(u)
        store_list(new_urls, "reachable_{}_filtred_across_years.txt".format(year))
        all_urls.update(urls)
        year += 2

def normal():
    year = 1997
    while (year < 2023):
        new_urls = []
        urls = read_list("reachable_{}_filtred.txt".format(year))
        for u in urls:
            s = normalize_url(u)
            if s not in new_urls:
                new_urls.append(s)

        store_list(new_urls, "reachable_{}_filtred_normalized.txt".format(year))
        year += 2

def main():
    normal()
    filterout()











if __name__ == "__main__":
    main()
