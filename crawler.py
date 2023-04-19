import requests, sys, pickle, os
from bs4 import BeautifulSoup
from queue import Queue
from threading import Thread

import config

site = 'https://chaturbate.com/'

settings = config.readConfig()
wishlist = settings['wishlist']
username = settings['username']
password = settings['password']

followed = []

def login():
    s.headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'referer': site,
        'origin': site.rstrip('/'),
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.8',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'content-type': 'application/x-www-form-urlencoded',
        }


    data = {'username': username, 'password': password, 'next': ''}
    result = s.get(site)
    soup = BeautifulSoup(result.text, "html.parser")
    data['csrfmiddlewaretoken'] = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')

    result = s.post(f'{site}auth/login/?next=/', data=data, cookies=result.cookies)
    if not checkLogin(result):
        print('login failed - please check your username and password is set correctly in the config file.')
        exit()
    else:
        print('logged in')


def checkLogin(result):
    soup = BeautifulSoup(result.text, "html.parser")
    if soup.find('div', {'id': 'user_information'}) is None:
        return False
    else:
        return True

def rememberSession():
    with open (sys.path[0] + "/" + username + '.pickle', 'wb') as f:
        pickle.dump(s, f)

def getModels():
    q = Queue()
    workers = []
    while not q.empty():
        for i in range(10):
            t = Thread(target=getOnlineModels)
            workers.append(t)
            t.start()
        for t in workers:
            t.join()

def getOnlineModels():
    page = 1
    while True:
        result = s.get(f'{site}followed-cams/?keywords=&page={page}')
        soup = BeautifulSoup(result.text, 'lxml')
        LIST = soup.findAll('ul', {'class': 'list'})[0]
        models = LIST.find_all('div', {'class': 'title'})
        for model in models:
            followed.append(model.find_all('a', href=True)[0].string.lower()[1:])
        try:
            if int(soup.findAll('li', {'class': 'active'})[1].string) >= int(soup.findAll('a', {'class': 'endless_page_link'})[-2].string):
                break
            else:
                page += 1
        except IndexError: break


if __name__ == '__main__':
    if os.path.exists(sys.path[0] + "/" + username + '.pickle'):
        with open(sys.path[0] + "/" + username + '.pickle', 'rb') as f:
            s = pickle.load(f)
    else:
        s = requests.session()
    result = s.get(site)
    if not checkLogin(result):
        login()

    getModels()
    print('{} followed models'.format(len(set(followed))))
    
    
