#!/usr/bin/env python



def read_list(file_name):
    urls = []
    with open(file_name) as f:
        [urls.append(line) for line in f.readlines()]
        return  urls

def store_list(urls:list, file_name:str):
    with open(file_name, 'w') as f:
        f.write("".join(urls))





def main():
    year = 1997
    all_urls = set()
    while (year < 2023):
        new_urls = []
        urls = read_list("./normalization_phase/reachable_{}_filtred_normalized.txt".format(year))
        for u in urls:
            if u not in all_urls:
                new_urls.append(u)
        print("the list for {} has {} elements".format(year,len(new_urls)))
        store_list(new_urls, "./filter_across_years_phase/reachable_{}_filtred_across_years.txt".format(year))
        all_urls.update(urls)
        year += 2











if __name__ == "__main__":
    main()
