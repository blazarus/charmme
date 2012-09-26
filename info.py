import urllib, urllib2, json
import util
import traceback


gi2loc = {"charm-4":"E14-6floor", "charm-2":"E14-5Floor-photobooth","charm-3":"BT Lab", "charm-6":"Telmex Lab", "charm-5":"E14-6floor"}

def get_recommendations(username):
    '''
    takes username of person (can be sponsor or medialabber)
    returns list of dictionary of both sponsors and medialabbers
      each dictionary's key -> value pairs:
	'name' -> string of fullname
   	'pic' -> string of url of image
	'affiliated' -> list of strings of group names
	'topics' -> list of strings of topics
	'location' -> string of location
    '''

    matches = {}
    matches = get_from_url('matches', "http://gi.media.mit.edu/luminoso2/match/people?person=" + username) if not '@' in username else get_from_url('matches', "http://gi.media.mit.edu/luminoso2/match/people?sponsor=" + username)
    if not matches:
	return []
    recs = []
    print "matches", matches
    for match in matches:
	user_info = get_user_info(match[unicode('person')])
	if not user_info:
	    continue
	user_info['weight'] = match[unicode('weight')]
	user_info['topics'] = match[unicode('terms')]
	recs.append(user_info)
    print "recs:", len(recs), recs
    return recs

def get_sponsor_recs(username):
    ''' same as get_recommendations except with sponsor '''
    matches = {} 
    matches = get_from_url('matches', "http://gi.media.mit.edu/luminoso2/match/sponsors?person=" + username) if not '@' in username else get_from_url('matches', "http://gi.media.mit.edu/luminoso2/match/sponsors?sponsor="+username)
    if not matches:
	return []
    recs = []

    for match in matches:
	print "match", match
        user_info = get_user_info(match[unicode('sponsor')])
	if not user_info:
	    continue
        user_info['weight'] = match[unicode('weight')]
	user_info['topics'] = match[unicode('terms')]
        recs.append(user_info)

    return recs
    
def get_user_info(username):
    '''
    returns dictionary with following key -> value pairs:
        'name' -> string of fullname
        'user_name' -> string of ML username
        'url' -> string of url of their personal website
        'picture_url' -> string of url of image
	'company' -> 
	'company_url' ->
        'affiliation' -> list of strings of group names
        'topics' -> list of strings of topics
        'last_loc' -> string of location
	'last_time' -> string of time last seen
    '''
    info = {}
    try:
    # if sponsor aka @ exist, query spm
    	if '@' in username:
            url = "http://data.media.mit.edu/spm/contacts/json?username=%s" % username
            data = json.loads(urllib2.urlopen(url).read().decode('latin1'))
            info = data['profile']
            info[u'name'] = info['first_name']+ " " + info['last_name']
            info[u'affiliation'] = info['mlid'] 
	# if no sponsor query people
        else:
            url = "http://data.media.mit.edu/people/json/?filter=(cn=%s)" % urllib.quote(username)
	    print "Url being used to look up user info:", url
            data = json.loads(urllib2.urlopen(url).read().decode('latin1'))
            info = data[0]
	    print "info received from url:", info

        info['picture_url'] = get_cached_img(150, info['picture_url'])
	info['last_loc'] = get_last_location(username)
#       print "after last loc", info['last_loc']
        if info['last_loc'] == "N/A":
            info['last_time'] = {}
	    info['last_loc'] = {}
        else:
            info['last_time'] = util.get_time_ago(info.get('last_loc').get('tstamp')) if info['last_loc'] else None
	info['topics'] = None	
	info['known'] = True

        #user_info_cache[username] = info
	print "info", info
        return info

    except Exception as e:
        print "user info error! probably doesn't exist...", type(e), e, username
	print "traceback", traceback.print_stack()
        info = {
            'user_name':username,
            'name':username,
            'picture_url': "http://pldb.media.mit.edu/face/%s" % username,
            'affiliation': None,
            'known': False   }
	print "returning none from get_user_info()"
	return None
    #user_info_cache[username] = info
    return info

def get_username(webcode):
    return get_from_url('username', "http://data.media.mit.edu/spm/contacts/json?web_code="+webcode)

def get_charms(email):
    return get_from_url('charms', 'http://tagnet.media.mit.edu/charms?user_name=' + email)

def get_last_location(username):
    events = get_from_url('events', 'http://gi-ego.media.mit.edu/%s/events/1' % username)
    if len(events) == 0: 
	return 'N/A'
    else:
	event = events[0]
	r = event.get('readerid')
	s = event.get('screenid')
	if r in gi2loc:   
            event['readerid'] = gi2loc[r]
        if s in gi2loc:
            event['readerid'] = gi2loc[s]
        #print event
        return event

def get_cached_img(size, src):
    base_url = "http://gi.media.mit.edu/imagecache/"
    return base_url+str(size)+"?src="+str(src)

def get_users_from_gi(screenid):
    tags = get_from_url('tags', "http://tagnet.media.mit.edu/getRfidUserProfiles?readerid="+screenid)
    if not tags:
	return []

    usernames = [tag['user_name'] for tag in tags]
    return usernames
 
def get_from_url(key, url):
    try:
	theurl = urllib2.urlopen(url).read()
	stream = json.loads(theurl)
    	if stream.get("error"):
	    print "get from url error!", "key:", key, "url:", url
	    return None
    	return stream[key]
    except urllib2.HTTPError:
	print "get from url error!", "key:", key, "url:", url
	print "traceback", traceback.print_stack()
	raise urllib2.HTTPError(None, None, None, None, None)

