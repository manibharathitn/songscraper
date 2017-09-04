# songscraper
scrap the songs from web


Options:
-l = is latest ?
-c = concurrency
-sp = start page
-ep = end page
-s = movie id start
-e = movie id end

Sample
python3 scrap.py -l -c 8
(Downloads songs from latest page with concurrency 8)

python3 scrap.py -sp 3 -ep 10 -c 10
(Downloads all the songs from page 3 to 10 with conurrency 10)
