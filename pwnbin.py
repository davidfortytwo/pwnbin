import time
import datetime
import sys
import getopt
import urllib.request
from bs4 import BeautifulSoup

def fetch_page(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        print(f"HTTP Error encountered: {e.code}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error encountered: {e.reason}")
        return None

def find_new_pastes(root_html):
    new_pastes = []
    menu = root_html.find('ul', {'class': 'right_menu'})
    if menu:
        for li in menu.find_all('li'):
            a_tag = li.find('a')
            if a_tag and 'href' in a_tag.attrs:
                paste_id = a_tag['href'].replace("/", "")
                new_pastes.append(paste_id)
    return new_pastes

def find_keywords(raw_url, keywords):
    paste_content = fetch_page(raw_url)
    if paste_content:
        for keyword in keywords:
            if keyword.lower().encode() in paste_content.lower():
                return True
    return False

def write_out(found_keywords, file_mode, file_name):
    if found_keywords:
        with open(file_name, file_mode) as f:
            for paste in found_keywords:
                f.write(f"{paste}\n")
        print(f"\nKeywords found in pastes have been saved to {file_name}")
    else:
        print("\nNo relevant pastes found. Exiting.")

def initialize_options(argv):
    keywords = {'ssh', 'pass', 'key', 'token'}
    file_name = 'log.txt'
    file_mode = 'w'  # Default to write mode
    run_time = None
    match_total = None
    crawl_total = None

    try:
        opts, args = getopt.getopt(argv, "hak:o:t:n:m:")
    except getopt.GetoptError:
        print('Usage: script.py -k <keyword1>,<keyword2>,... -o <outputfile> [-a] [-t <runtime>] [-n <crawl_total>] [-m <match_total>]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage: script.py -k <keyword1>,<keyword2>,... -o <outputfile> [-a] [-t <runtime>] [-n <crawl_total>] [-m <match_total>]')
            sys.exit()
        elif opt == '-a':
            file_mode = 'a'  # Append mode
        elif opt == "-k":
            keywords = set(arg.split(","))
        elif opt == "-o":
            file_name = arg
        elif opt == "-t":
            run_time = int(arg)
        elif opt == '-m':
            match_total = int(arg)
        elif opt == '-n':
            crawl_total = int(arg)

    return file_name, keywords, file_mode, run_time, match_total, crawl_total

def main(argv):
    file_name, keywords, file_mode, run_time, match_total, crawl_total = initialize_options(argv)
    root_url = 'https://pastebin.com'
    raw_url = 'https://pastebin.com/raw/'
    paste_list = set()
    found_keywords = []

    start_time = datetime.datetime.now()
    print(f"\nCrawling {root_url}. Press ctrl+c to save results to {file_name}")

    try:
        while True:
            root_html = BeautifulSoup(fetch_page(root_url), 'html.parser')
            for paste in find_new_pastes(root_html):
                if paste not in paste_list:
                    paste_list.add(paste)
                    if find_keywords(raw_url + paste, keywords):
                        found_keywords.append(raw_url + paste)
                        print(f"Keyword found in paste: {raw_url + paste}")

            if run_time and (datetime.datetime.now() - start_time).seconds > run_time:
                print("\nReached runtime limit.")
                break

            if match_total and len(found_keywords) >= match_total:
                print("\nReached match total limit.")
                break

            if crawl_total and len(paste_list) >= crawl_total:
                print("\nReached crawl total limit.")
                break

            time.sleep(10)  # Sleep to avoid excessive requests

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")

    finally:
        write_out(found_keywords, file_mode, file_name)

if __name__ == "__main__":
    main(sys.argv[1:])

