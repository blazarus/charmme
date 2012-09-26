from flask import Flask, render_template, request, redirect, url_for, flash
from fromcharms import sponsor_category, sponsor_rec, get_charms, get_last_location
import json
import urllib, urllib2
import socket
import nltk
app = Flask(__name__)
app.secret_key = "NbNn4fpyT+pNKOL2gEKqo/dUvId7WzKc"
from use_lumie_study import get_related_people, get_related_concepts, \
get_related_projects, intersect_related_concepts, model, make_user_vec, vec_for_phrase
import datetime, time

user_info_cache = {}

blacklist = ['mind common', 'everyone room', 'dynamic way', 'beyond', 'use',
             'approach', 'collect hundred', 'hundred', 'thousand',
             'hundred thousand', 'korean', 'exploit', 'develop', 'new',
             'various way', 'date everyone', 'enable', 'leverage', 'tool use',
             'various', 'project explore', 'sponsor', 'technique', 'allow', 'allow user']

def get_time_ago(then):
    t = datetime.datetime(*time.strptime(then, "%Y-%m-%d %H:%M:%S")[0:7])
    now = datetime.datetime.now()
    diff = now - t
    minutes, seconds = divmod(diff.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    res = ""
    if diff.days > 0:
        res += ("%d days "% diff.days) if diff.days > 1 else "1 day "
    elif hours > 0:
        res += ("%d hours "% hours) if hours >1 else "1 hour " 
    elif minutes > 0:
        res += ("%d minutes " % minutes) if minutes > 1 else "1 minute "
    elif seconds > 0:
        res += ("%d seconds " % seconds) if seconds > 1 else "1 second "

    return res+"ago"

def get_cached_img(size, src):
    base_url = "http://gi.media.mit.edu/imagecache/"
    return base_url+str(size)+"?src="+str(src)



def get_user_info(username):
    start = time.time()
    if username in user_info_cache: return user_info_cache[username]
    data = None
    info = dict()
    try: 
        # if sponsor aka @ exist, query spm
	if '@' in username:
	    #print "sponsor!"
	    url = "http://data.media.mit.edu/spm/contacts/json?username=%s" % username
            data = json.loads(urllib2.urlopen(url).read().decode('latin1'))
#	    print "data", data
	    info = data['profile']
#	    print info
	    info[u'name'] = info['first_name']+ " " + info['last_name']
	    info[u'affiliation'] = info['mlid']
        # if no sponsor query people
	else:   	 
    	    url = "http://data.media.mit.edu/people/json/?filter=(cn=%s)" % urllib.quote(username)
	    data = json.loads(urllib2.urlopen(url).read().decode('latin1'))
#	    print "len of data", len(data)
#	    if len(data) == 0:
#		print data
	    info = data[0]

#	print info
#        print
#	print info['name']
	info['picture_url'] = get_cached_img(150, info['picture_url'])
#	print "after picture"
	info['last_loc'] = get_last_location(username)
#	print "after last loc", info['last_loc']
	if info['last_loc'] == "N/A":
	    info['last_time'] = "N/A"
	else:
	    info['last_time'] = get_time_ago(info.get('last_loc').get('tstamp')) if info['last_loc'] else None
	
#	print "after last time", info['last_time']
        #if isinstance(info['affiliation'], list):
        #    info['affiliation'] = ', '.join(info['affiliation'])


        info['known'] = True

	user_info_cache[username] = info	
	return info
  
    except Exception as e:
	print "user info error!", type(e), e, username
	info = {
	    'username':username,
	    'name':username,
	    'picture_url': "http://pldb.media.mit.edu/face/%s" % username, 
	    'affiliation': None, 
	    'known': False   }
    user_info_cache[username] = info
    return info

def get_user_info_works(username):

    start = time.time()
    # if in cache already, return that
    if username in user_info_cache: return user_info_cache[username]

    try:
	data = json.load(urllib2.urlopen('http://tagnet.media.mit.edu/users?user_name=%s&capability=profile' % urllib.quote(username)))['profile']
	info = dict(
         	username=username,
                name=data['name'],
                picture_url=get_cached_img(150, data['picture_url']),
		url = data['url'],
                affiliation=', '.join(data['affiliation']),
		usertype=data.get('user_type'),
		last_loc=get_last_location(username),
		company=data.get('company_name'),
		company_url = data.get('company_url'),
		known=True)
    except Exception:
	info = {
                'username': username,
                'name': username,
                'picture_url': "http://pldb.media.mit.edu/face/nobody",
                'known': False}
     
    info['last_time'] = get_time_ago(info.get('last_loc').get('tstamp')) if 'last_loc' in info else None


    #get cached version of picture
    user_info_cache[username] = info

#    print "get_user_info took", time.time()-start
    return info

def distance(x1, x2):

    if x1 == x2:
	return 0

    if x1 == "Telmex Lab":
	x1 = "e14-474-1"
    if x2 == "Telmex Lab":
	x2 = "e14-474-1"

    if x1 == "BT Lab":
	x1 = "e14-320-1" # TODO confirm
    if x2 == "BT Lab":
	x2 = "e14-320-1"
    #get bldg
    x1_bldg = x1[:3]
    x2_bldg = x2[:3]
    
    # get floor
    x1_fl = int(x1[4])
    x2_fl = int(x2[4])
 
    score = 0

    if x1_bldg != x2_bldg:
	score += 10

    score += abs(x1_fl - x2_fl)
#    print "vjw: score", score, "from ", x1
    return score

def get_user_info_ORIG(username):
    if username in user_info_cache: return user_info_cache[username]
    if '@' in username:
        try:
            data = json.load(urllib2.urlopen('http://tagnet.media.mit.edu/users?user_name=%s&capability=profile' % urllib.quote(username)))['profile']
            info = dict(
                username=username,
                name=data['name'],
                picture_url=data['picture_url'],
                affiliation=', '.join(data['affiliation']),
		usertype=data.get('user_type'),
		sponsor=data.get("sponsor"), 
		company=data.get("company_name"), 
		company_url = data.get("company_url"), 
                known=True)
            user_info_cache[username] = info
            return info
        except Exception:
            # handle sponsors:
            info = {
                'username': username,
                'name': username,
                'picture_url': "http://pldb.media.mit.edu/face/nobody",
                'known': False,
		'usertype':data.get('user_type'),
		'sponsor':data.get("sponsor"),
                }
            return info
    try:
        url = "http://data.media.mit.edu/people/json/?filter=(cn=%s)" % urllib.quote(username)
#	print url
        data = json.loads(urllib2.urlopen(url).read().decode('latin1'))
        info = data[0]
        info['name'] = info['name'].encode('latin1', 'replace').decode('utf-8', 'replace') # Usernames are actually utf-8. Undo latin1-ization.
        info['known'] = True
        if isinstance(info['affiliation'], list):
            info['affiliation'] = ', '.join(info['affiliation'])
    except IndexError:
        info = {
            'username': username,
            'name': username,
            'picture_url': "http://pldb.media.mit.edu/face/%s" % username,
            'affiliation': None,
            'known': False
        }
    user_info_cache[username] = info
    return info

def intersect(list1, list2):
    if isinstance(list1, basestring): list1 = list1.split(', ')
    if isinstance(list2, basestring): list2 = list2.split(', ')
    return set(list1) & set(list2)

def is_noun_phrase(phrase):
    """
    Use NLTK to guess whether this is a noun phrase.
    """

    tagged = nltk.pos_tag(phrase.split())
    last_tag = tagged[-1][1]
    return (last_tag.startswith('NN') or last_tag == 'VBG')

def list_phrases(concept_list, n=8):
    """
    Make a natural-languagey list of phrases from a list of top concepts.
    This should perhaps be split out into another module.
    """
    def smash(text):
        """
        A blunt hammer for finding when un-normalized phrases are too similar.
        """
        return text.lower().replace('-', ' ')

    phrases = []
    for concept, weight in concept_list:
        if concept in blacklist:
            continue
        if weight > 0:
            count = model.database.count_term(concept)
            expanded = model.database.get_term_text(concept)
            if count > 1 and expanded and is_noun_phrase(expanded):
                # check to see if the phrase is a superset or subset of another
                # phrase in the list
                dup = False
                for i in xrange(len(phrases)):
                    existing = phrases[i]
                    if smash(existing).find(smash(expanded)[:-1]) > -1:
                        dup = True
                        break
                    elif smash(expanded).find(smash(existing)[:-1]) > -1:
                        phrases[i] = expanded
                        dup = True
                        break
                if not dup: phrases.append(expanded)
                if len(phrases) == n: break
    return ', '.join(phrases)

def list_concepts(concept_list):
    return ', '.join(x[0] for x in concept_list if x[1] > 0)


