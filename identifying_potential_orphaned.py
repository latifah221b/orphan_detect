
import json

def store_json(file_name,all_urls):
    with open(file_name, 'w') as fp:
        json.dump(all_urls, fp, sort_keys=True, indent=4)

def read_json(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
    return  data


def main():

    year = 1997
    while year < 2007:
        json_list = [];
        jsons = read_json("./estimation_phase/{}_compersion.json".format(year))
        for j in jsons:
            if int(j["last_archived_version"]) < 2016:
                json_list.append(j)
        print("{} has {} potential orphaned pages".format(year, len(json_list)))
        store_json("./potential_orphaned_urls/{}_potential_orphaned.json".format(year), json_list)
        year += 2


if __name__ == "__main__":
    main()