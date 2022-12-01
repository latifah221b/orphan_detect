
def normalize_url(url):
    url = url.replace("http://www.", "")
    url = url.replace(":80","")
    url = url.replace("http://","")
    url = url.replace("https://","")
    return url


def read_list(file_name):
    urls = []
    with open(file_name) as f:
        [urls.append(line) for line in f.readlines()]
        return  urls

def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write("".join(urls))





def main():
    # this aims to normalizs the urls and remove any duplicate.
    year = 1997
    while (year < 2023):
        new_urls = []
        urls = read_list("./error_pages_removing/reachable_{}_filtred.txt".format(year))
        for u in urls:
            s = normalize_url(u)
            if s not in new_urls:
                new_urls.append(s)
        print("the list of year {} after normalization: {}".format(year,len(new_urls)))
        store_list(new_urls, "./normalization_phase/reachable_{}_filtred_normalized.txt".format(year))
        year += 2



if __name__ == "__main__":
    main()