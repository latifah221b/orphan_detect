


def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write("".join(urls))



def read_list(file_name):
    urls = []
    with open(file_name) as f:
        [urls.append(line) for line in f.readlines()]
        return  urls

def main():
    year = 1997
    while (year < 2023):
        new_urls = []
        urls = read_list("./tobeScanned_urls/{}.txt".format(year))
        for u in urls:
            new_urls.append(u.replace("https://cs.brown.edu/",""))
        print("the list for {} has {} elements".format(year,len(new_urls)))
        store_list(new_urls, "./test/test_{}.txt".format(year))
        year += 2


if __name__ == "__main__":
    main()