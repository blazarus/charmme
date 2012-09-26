from use_lumie_study import get_related_people, make_documents_vec
from csc import divisi2
import urllib2, json
from charm_exceptions import *

#class AntiSocialException(Exception): pass

#class NotYourEmailException(Exception): pass

gi2loc = {"charm-4":"E14-6floor", "charm-2":"E14-5Floor-photobooth","charm-3":"BT Lab", "charm-6":"Telmex Lab", "charm-5":"E14-6floor"}
		

def get_charms(email):
    url = 'http://tagnet.media.mit.edu/charms?user_name=' + email
    try:
        theurl = urllib2.urlopen(url).read()
        stream = json.loads(theurl)
    except urllib2.HTTPError:
	print "not your mail exception"
        raise NotYourEmailException
    if stream.get("error"): 
	print "not your email exception"
	raise NotYourEmailException
    print "charms len", len(stream['charms'])
    return stream['charms']


def get_username(webcode):
    url = "http://data.media.mit.edu/spm/contacts/json?web_code="+webcode
    try:
	theurl = urllib2.urlopen(url).read()
	stream = json.loads(theurl)
    except urllib2.HTTPError:
	#raise Exception
	print "error!"
    if stream.get("error"): 
	print "error!"
	#raise Exception
    return stream['username']

def get_last_location(username):
    url = 'http://gi-ego.media.mit.edu/%s/events'%username
    try:
	theurl = urllib2.urlopen(url).read()
	stream = json.loads(theurl)
    except urllib2.HTTPError:
	print "http error"
	raise Exception
    if stream.get("error"):
	print "stream error!"
	raise Exception
    events = stream['events']
    if len(events) == 0: return 'N/A'
    else:
	event = events[0]
	r = event.get('readerid')
	s = event.get('screenid')
#	print event['readerid'] in gi2loc, c, gi2loc.get(c)
	if r in gi2loc:
	    event['readerid'] = gi2loc[r]
	if s in gi2loc:
	    event['readerid'] = gi2loc[s]
	#print event
	return event

def sponsor_proj_list(email):
    charms = get_charms(email)
    if not charms:
        raise AntiSocialException
    ids = ['PLDBDocs/'+x['id']+'.txt' for x in charms]
    return ids
	
def sponsor_rec(email, n=20):
    # FIXME
    ids = sponsor_proj_list(email)
    return get_related_people(ids, n)

def sponsor_category(email):
    return make_documents_vec(sponsor_proj_list(email))
