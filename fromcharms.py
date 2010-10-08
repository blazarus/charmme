from use_lumie_study import get_related_people
from csc import divisi2
import urllib2, json

class AntiSocialException(Exception): pass

class NotYourEmailException(Exception): pass

def sponsor_proj_list(email):
    url = 'http://tagnet.media.mit.edu/' + email +'/charms'
    theurl = urllib2.urlopen(url).read()
    stream = json.loads(theurl)
    if stream.get("error"): raise NotYourEmailException
    charms = stream['charms']
    if charms == []:
        raise AntiSocialException
    ids = [x['id']+'.txt' for x in charms]
    return ids

def sponsor_rec(email, n=20):
    ids = sponsor_proj_list(email)
    return get_related_people(ids, n)

def sponsor_category(email):
    return divisi2.SparseVector.from_counts(sponsor_proj_list(email))
