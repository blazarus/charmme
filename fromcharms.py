from use_lumie_study import get_related_people
import urllib2, json

class AntiSocialException(Exception): pass

class NotYourEmailException(Exception): pass

def sponsor_rec(email, n=20):
    url = 'http://tagnet.media.mit.edu/' + email +'/charms'
    theurl = urllib2.urlopen(url).read()
    stream = json.loads(theurl)
    if "error" in stream: raise NotYourEmailException
    charms = stream['charms']
    if not charms:
        raise AntiSocialException
    ids = [x[id]+'.txt' for x in charms]
    return get_related_people(ids, n)
