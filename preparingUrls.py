import re
import json

def addhttps(url:str):
    if not re.match('(?:http|ftp|https)://', url):
        url = 'https://{}'.format(url)
    return url

def store_json(file_name,all_urls):
    with open(file_name, 'w') as fp:
        json.dump(all_urls, fp, sort_keys=True, indent=4)

def read_json(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
    return  data

def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write("".join(urls))
def main():

    year = 1997
    while (year < 2023):
        new_urls = []
        urls = read_json("./redirect_test/noneredirect_{}.json".format(year))
        for u in urls:
            s = addhttps(u["url"])
            new_urls.append(s)
        print("the list {} length is {}".format(year,len(new_urls)))
        store_list(new_urls, "./tobeScanned_urls/{}.txt".format(year))
        year += 2



if __name__ == "__main__":
    main()