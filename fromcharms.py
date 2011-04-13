from use_lumie_study import get_related_people, make_documents_vec
from csc import divisi2
import urllib2, json

class AntiSocialException(Exception): pass

class NotYourEmailException(Exception): pass

def sponsor_proj_list(email):
    url = 'http://tagnet.media.mit.edu/charms?user_name=' + email
    try:
        theurl = urllib2.urlopen(url).read()
        stream = json.loads(theurl)
    except urllib2.HTTPError:
        raise NotYourEmailException
    if stream.get("error"): raise NotYourEmailException
    charms = stream['charms']
    if not charms:
        raise AntiSocialException
    ids = ['models/PLDBStudy/Documents/'+x['id']+'.txt' for x in charms]
    return ids

def sponsor_rec(email, n=20):
    # FIXME
    ids = sponsor_proj_list(email)
    return get_related_people(ids, n)

def sponsor_category(email):
    return make_documents_vec(sponsor_proj_list(email))
