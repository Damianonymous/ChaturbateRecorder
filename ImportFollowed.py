import requests, configparser, sys, pickle, os
from bs4 import BeautifulSoup



followed = []

Config = configparser.ConfigParser()
Config.read(sys.path[0] + "/config.conf")
wishlist = Config.get('paths', 'wishlist')
username = Config.get('login', 'username')
password = Config.get('login', 'password')


def login():
    s.headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'referer': 'https://chaturbate.com/',
        'origin': 'https://chaturbate.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.8',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'content-type': 'application/x-www-form-urlencoded',
        }


    data = {'username': username, 'password': password, 'next': ''}
    result = s.get("https://chaturbate.com/")
    soup = BeautifulSoup(result.text, "html.parser")
    data['csrfmiddlewaretoken'] = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')

    result = s.post('https://chaturbate.com/auth/login/?next=/', data=data, cookies=result.cookies)
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

def getModels():
    print("getting followed models...")
    page = 1
    while True:
        result = s.get('https://chaturbate.com/followed-cams/?keywords=&page={}'.format(page))
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
    result = s.get('https://chaturbate.com/')
    if not checkLogin(result):
        login()
    getModels()
    print('{} followed models'.format(len(set(followed))))
    f = open(wishlist, 'r')
    wanted = list(set(f.readlines()))
    wanted = [m.strip('\n').split('chaturbate.com/')[-1].lower().strip().replace('/', '') for m in wanted]
    print('{} models currently in the wanted list'.format(len(wanted)))
    followed.extend(wanted)
    f= open(wishlist, 'w')
    for model in set(followed):
        f.write(model + '\n')
    print('{} models have been added to the wanted list'.format(len(set(followed)) - len(set(wanted))))
    with open (sys.path[0] + "/" +username + '.pickle', 'wb') as f:
        pickle.dump(s, f)
