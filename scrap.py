import requests
import re, zipfile, os
import concurrent.futures
import argparse
parser = argparse.ArgumentParser()

parser.add_argument('-s', dest='start', default=1, help='Start MovieId (default: 1)')
parser.add_argument('-e', dest='end', default=2, help='End MovieId (default: 2)')
parser.add_argument('-sp', dest='start_page', default=1, help='Start page (default: 1)')
parser.add_argument('-ep', dest='end_page', default=2, help='End page (default: 2)')
parser.add_argument('-l', dest='latest', action='store_true', help='Download latest songs')
parser.add_argument('-H', dest='home_page', action='store_true', help='Download home page songs')

parser.add_argument('-c', dest='concurrency', default=1, help='Concurrency (default: 1)')

args = parser.parse_args()

BASE_URL = 'https://www.sunmusiq.com/'


def isDuplicate(movieId, n_songs):
    return movieId in existing_movie_ids and existing_movie_ids[movieId] >= n_songs

def scrap(url, movie_id):

    req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

    html = req.content.decode()
    movie = re.search('<title>([^\(]*)', html).group(1).strip()
    n_songs = html.count("/mp3-download/download")

    if isDuplicate(movie_id, n_songs):
        print("Up to date {}".format(movie))
        return

    link = re.findall('http://www.starfile.info/download-7s-zip-new/\?Token=[\w=]*', html)[-1]
    req = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}) #with cookie

    link = link.replace('download-7s-zip-new/', 'download-7s-zip-new/download-3.ashx')

    print('Downloading {} ...'.format(movie))
    req = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)

    zip_file_name = "{}.zip".format(movie_id)
    with open(zip_file_name, "wb") as f:
        for block in req.iter_content(1024):
            f.write(block)

    with zipfile.ZipFile(zip_file_name) as zip_ref:
        zip_ref.extractall()

    # Cleaning the zip file
    os.remove(zip_file_name)
    new_movie_ids[movie_id] = n_songs

def getIdsFromPage(st, en, url):
    id_list = []
    pg_list = [url.format(pg) for pg in range(int(st), int(en))]
    for pg_url in pg_list:
        req = requests.get(pg_url, headers={'User-Agent': 'Mozilla/5.0'})

        html = req.content.decode()
        id_list.extend(re.findall('([0-9]+)-starmusiq-download', html))
    return list(set([ int(i_d) for i_d in id_list]))

def getUrls():
    id_list = range(int(args.start), int(args.end))
    if args.latest:
        id_list = getIdsFromPage(args.start_page, args.end_page, BASE_URL + 'latest.asp?pgNo={}')
    elif args.home_page:
        id_list = getIdsFromPage(1, 7, BASE_URL + '?pgNo={}')

    elif args.start_page != 0 and args.end_page != 0 and args.start == 1 and args.end == 2:
        id_list = getIdsFromPage(args.start_page, args.end_page, BASE_URL + 'mp3-database.asp?pgNo={}')
    URLS = [(BASE_URL + 'tamil_movie_songs_listen_download.asp?MovieId={}'.format(movieId), movieId) for movieId in id_list]
    return URLS

existing_movie_ids = {}
new_movie_ids = {}

def read_file_into_dict():
    with open("ids.txt") as f:
        for line in f:
            key, value = line.split(",")
            key, value = int(key.strip()), int(value.strip())
            if key:
                existing_movie_ids[key] = value

def write_dict_into_file():
    existing_movie_ids.update(new_movie_ids)
    with open("ids.txt", "w") as f:
        for key,val in existing_movie_ids.items():
            f.write("{},{}\n".format(key,val))

with concurrent.futures.ThreadPoolExecutor(max_workers=int(args.concurrency)) as executor:
    read_file_into_dict()
    future_to_url = {executor.submit(scrap, url, ind): url for url, ind in getUrls()}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r Failed: %s' % (url, exc))
    write_dict_into_file()