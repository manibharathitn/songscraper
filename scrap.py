from urllib.request import Request, urlopen
import re, zipfile, os
import concurrent.futures
import argparse
parser = argparse.ArgumentParser()

parser.add_argument('-s', dest='start', default=1, help='Start MovieId (default: 1)')
parser.add_argument('-e', dest='end', default=2, help='End MovieId (default: 2)')
parser.add_argument('-sp', dest='start_page', default=1, help='Start MovieId (default: 1)')
parser.add_argument('-ep', dest='end_page', default=2, help='End MovieId (default: 2)')
parser.add_argument('-l', dest='latest', action='store_true', help='Download latest songs')

parser.add_argument('-c', dest='concurrency', default=1, help='Concurrency (default: 1)')

args = parser.parse_args()

def scrap(url, movieId):

    with open("ids.txt", "a+") as f:
        f.seek(0)
        if len(re.findall('[\\n]?{}\n'.format(movieId), f.read())) > 0:
            print('Already downloaded {} ...'.format(movieId))
            return
        f.writelines("{}\n".format(movieId))

    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    r = urlopen(req)

    cook = r.getheader('Set-Cookie')
    html = str(r.read())
    movie = re.search('<title>([\w ]*) \(', html).group(1)
    link = re.findall('http://www.starfile.info/download-7s-zip-new/\?Token=[\w=]*', html)[-1]
    req = Request(link, headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cook})
    page = urlopen(req)


    cook = page.getheader('Set-Cookie')
    link = link.replace('download-7s-zip-new/', 'download-7s-zip-new/download-3.ashx')
    req = Request(link, headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cook})
    print('Downloading {} ...'.format(movie))
    page = urlopen(req).read()

    with open("{}.zip".format(movieId), "wb") as f:
        f.write(page)
        with zipfile.ZipFile("{}.zip".format(movieId), "r") as zip_ref:
            zip_ref.extractall()

    # Cleaning the zip file
    os.remove("{}.zip".format(movieId))

def getIdsFromPage(st, en, url):
    id_list = []
    pg_list = [url.format(pg) for pg in range(int(st), int(en))]
    for pg_url in pg_list:
        req = Request(pg_url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urlopen(req)

        html = str(r.read())
        id_list.extend(re.findall('MovieId=([0-9]+)', html))
    return list(set([ int(i_d) for i_d in id_list]))

def getUrls():
    id_list = range(int(args.start), int(args.end))
    if args.latest:
        id_list = getIdsFromPage(args.start_page, args.end_page, 'http://www.sunmusiq.com/latest.asp?pgNo={}')
    elif args.start_page != 0 and args.end_page != 0:
        id_list = getIdsFromPage(args.start_page, args.end_page, 'http://sunmusiq.com/mp3-database.asp?pgNo={}')
    URLS = [('http://www.sunmusiq.com/tamil_movie_songs_listen_download.asp?MovieId={}'.format(movieId), movieId) for movieId in id_list]
    return URLS

with concurrent.futures.ThreadPoolExecutor(max_workers=int(args.concurrency)) as executor:
    future_to_url = {executor.submit(scrap, url, ind): url for url, ind in getUrls()}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r Failed: %s' % (url, exc))
