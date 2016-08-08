import requests
import argparse
import re
import json

check_api = 'https://club.pokemon.com/api/signup/verify-username'

s = requests.session()


def touch():
    headers={  # No headers required
                    'Host': 'club.pokemon.com',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch, br',
                    'Accept-Language': 'en-US,en;q=0.8',
                }
    r = s.get('https://club.pokemon.com/', headers=headers)
    print r.content
    relic = re.search('loader_config={xpid:".*"};window.NREUM', r.content)
    relic = re.sub('.*xpid:"', '', relic.group(0))
    relic = re.sub('"}.*', '', relic)
    return s.cookies['csrftoken'], relic


def check(username, csrftoken, relic):
    head = {
        'X-CSRFToken': csrftoken,
        'User-Agent': 'Mozilla/5.0  (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4',
        'X-NewRelic-ID': relic,
        'Content-Type': 'application/json'
    }
    i = '{"name":"%s"}' %(username)
    r = s.post(check_api, data=i, headers=head)
    return json.loads(r.content)['inuse']


def main():
    csrftoken, relic = touch()
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="Username", required=False, default="mapDefender0")
    args = parser.parse_args()
    if check(args.username, csrftoken, relic):
        print '[-] username {0} taken'.format(args.username)
    else:
        print '[+] username {0} available'.format(args.username)

if __name__ == '__main__':
    main()