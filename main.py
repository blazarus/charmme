from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, g
from charm_exceptions import AntiSocialException, NotYourEmailException, InactiveCharmsException
import json
import urllib, urllib2
import socket
app = Flask(__name__)
app.secret_key = '\x87WI]\xa4\xb99\x0b\xf7B<9\xc6)\x8b\xc5`\xf8\xfbv\x8a\xefO\xf1'

import time
import datetime
from connectme import intersect, is_noun_phrase, list_phrases, list_concepts, distance
import random
from info import get_user_info, get_recommendations, get_sponsor_recs, get_charms, get_users_from_gi, get_username
import util
import sqlite3
DATABASE = "charmme.sqlite"
#how long to keep in cache, in seconds
PERSON_INFO_CACHE_TIME = 86400 #1 day
REC_CACHE_TIME = 3600 #1 hour

def connect_db():
    return sqlite3.connect(DATABASE)
	
from contextlib import closing
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()
	
@app.before_request
def before_request():
    g.db = connect_db()

@app.after_request
def after_request(response):
    g.db.close()
    return response



user_info_cache = {}
recs_cache = {}
sponsor_recs_cache = {}
charms_cache = {}

names_cache = []
infos_cache = []

port = 3000
survey_size = 66

eval_dir = "./eval/"

myinfo = dict(username="vjw", name="victor j wang", picture_url="", affiliation="", known=True)

blacklist = ['mind common', 'everyone room', 'dynamic way', 'beyond', 'use',
             'approach', 'collect hundred', 'hundred', 'thousand',
             'hundred thousand', 'korean', 'exploit', 'develop', 'new',
             'various way', 'date everyone', 'enable', 'leverage', 'tool use',
             'various', 'project explore', 'sponsor', 'technique', 'allow', 'allow user']

# returns boolean of 
def ancient(timestr):
    if not isinstance(timestr, str): return False
    if timestr == "N/A": return True
    s = timestr.split(" ")

#    print "s[0]", s[0]
    val = int(s[0])
    t = s[1]
    return s > 3 and t == "days" 

@app.route('/from_gi/<username>')
def from_gi(username=None):
    print "gi reroute", username
    if username == None:
	return redirect(url_for('login'))
    resp = make_response(redirect(url_for('profile', username=username)))
    resp.set_cookie('username', username)
    return resp 

@app.route('/gi/<screenid>')
def gi(screenid=None):
    # get list of people standing infront of screenid 
    users = get_users_from_gi(screenid)
    if len(users) == 1:
	username = users[0]
	resp = make_response( redirect(url_for('profile', username=users[0])) )
	resp.set_cookie('username', users[0])
	return resp
    return render_template('login.html', users=users)

@app.route('/')
def index():
    username = request.cookies.get('username')
    webcode = request.cookies.get('web_code')
    print "username", username, "webcode", webcode
    if request.method == 'POST':
	print "post from GI detected"
	uname = request.form['value']
	resp = make_response( redirect(url_for('profile', username=uname)))
	resp.set_cookie('username', uname)
	return resp
    if webcode == None and username == None:
        print "first time user! no cookie and webcode"
	return redirect(url_for('login'))
    else:
	username = get_username(webcode)
	if username == None:
	    print "username is none from webcode"
	    return redirect(url_for('login'))
	print "returning user!", username
	resp = make_response( redirect(url_for('profile', username=username)))
	resp.set_cookie('username', username)
	return resp

def indexOld():
    print 'webcode??', request.cookies.get('web_code')
    print session
    #TODO must differentiate between redirecting skip from qr OR user landed here directly
    print "cookie webcode", request.cookies.get('web_code')
    if request.cookies.get('web_code') == None:
	return redirect(url_for('login'))
    if request.cookies.get('web_code') != None:
	my_webcode = request.cookies['web_code']
	username = get_username(my_webcode)	
	print "username", username
#	return redirect(url_for('profile', username=username))
        # go to user's profile
        #return 'Logged in as %s' % escape(session['my_webcode'])

#    if 'web_code' in request.cookies:
#	username = get_username(session['my_webcode'])
#	print "in here", username
	resp = make_response( redirect(url_for('profile', username=username)))
	resp.set_cookie('username', username)
	return resp
    #return redirect("http://qr.media.mit.edu/login?next=http://charmme.media.mit.edu/&noskip=true")    
    return redirect(url_for('login'))

# should never be called
@app.route('/login', methods=['GET', 'POST'])
def login(users=None):
    if request.method == 'POST':
	print "post detected"
	resp = make_response( redirect(url_for('index')))
	resp.set_cookie('web_code', request.form['my_webcode'])
        return resp
    return render_template("login.html")

@app.route('/profile/<username>/')
def profile(username):
    resp = make_response( render_template("profile_loading.html"))
    home_username = request.cookies.get('username')
    resp.set_cookie('username', home_username)
    return resp


@app.route('/profile/<username>/data/')
def profile_data(username):
    start = time.time()
    home_username = request.cookies.get('username')
    myprofile = home_username == username
    print "returning user?", myprofile, username
    print "met", request.cookies
# TODO test if webcode belongs to session. self profile diff view vs others
#TODO package user's info into dictionary

    yourself = retrieve_yourself(username)

    try:
	user_charms = get_charms(username)
    except AntiSocialException:
	if home_username == username:
	    flash(u"You don't have any charms yet. Go out and meet people!", 'error')
	    print "No Charms!"
	    return render_template('error.html', message="You don't have any charms! We need to know something about you before we can recommend anyone. To charm something, take a picture of a project or session QR Code using a QR Reader application. A good QR Reader to download is Google Goggles.")
	else:
	    print "has no charms", username
	    return render_template('error.html', message = "Also, this user does not have any charms. ")
    except InactiveCharmsException:
	print "inactive charm exception"
	return render_template('error.html', message="Unfortunately, the projects you have charmed are no longer active. Go charm new projects!") 
    except Exception as e:
	print "error1", type(e), e
	flash(u"error", 'error')
	return render_template('error.html', message="We are working on a fix right now.")

    yourself['num_charms']= len(user_charms)
    user_charms.reverse()
    yourself['charms'] = user_charms

    # visiting guest profile
    if not myprofile:
        resp = make_response( render_template("profile.html", yourself=yourself, recommendations=[],
                                sponsor_recs=[], home_username=home_username, my_profile=False))
	resp.set_cookie('username', home_username)
	print "profile load time: ", time.time() - start
	return resp

    recommendations = retrieve_recommendations(username, yourself) 

    sponsor_recs = retrieve_sponsor_recs(username, yourself)

    if not recommendations:
        flash(u"Sorry, %s, I don't know who you are." % username, 'error')
        return render_template('error.html', message="Sorry about that.")
    
    if username == 'joi':
	yourself['affiliation'] = 'Director'
    resp = make_response( render_template("profile.html", yourself=yourself, recommendations=recommendations,
				sponsor_recs=sponsor_recs, home_username=home_username, my_profile=True))
    resp.set_cookie('username', home_username)
    print "profile load time: ", time.time() - start, "\n\n\n\n\n"
    return resp

def retrieve_yourself(username):
    curs = g.db.execute("SELECT username, info, update_time, linkedin_id FROM users WHERE users.username = ?;", (username,))
    result = curs.fetchone()
    print "Result of querying db for 'yourself':", result
    if result and len(result) > 0 and result[0] and eval(result[1]) and time.time()-result[2] < PERSON_INFO_CACHE_TIME:
        print "Using cache for 'yourself' info"
        yourself = eval(result[1])
        print "'yourself' info from DB cache:", yourself
    else:
        try:
            print "Querying GI for 'yourself' info"
            yourself = get_user_info(username)
    	    print "yourself:", yourself
    	    #Mimick an 'insert or update' using the integrity exception
    	    try:
                g.db.execute("INSERT INTO users (username, info, update_time) VALUES (?,?,?);", (username, str(yourself), time.time()))
            except sqlite3.IntegrityError, m:
                g.db.execute("UPDATE users SET info=?, update_time=? WHERE username=?", (str(yourself), time.time(), username))

            g.db.commit()
        except urllib2.HTTPError:
            return render_template('error.html', message="Sorry, our system is currently down. Try again later.")
    return yourself

def retrieve_recommendations(username, yourself):
    #get media lab recommendations
    curs = g.db.execute("SELECT rec.username, rec.info, rec.update_time, rec.linkedin_id, recommendations.update_time"\
        +" FROM users AS yourself, users AS rec, recommendations"\
        +" WHERE yourself.username = ? AND recommendations.yourself = yourself.username AND recommendations.recommendation = rec.username;", (username,))
    result = curs.fetchall()
    print "Result of querying db for recommendations:", result
    use_cache = len(result) > 0
    curr_time = time.time()
    for res in result:
        if not (res and res[1] and curr_time-res[4] < REC_CACHE_TIME):
            use_cache = False
    if use_cache:
        print "Using cache for recommendations"
        recommendations = [eval(person[1]) for person in result]
    else:
        try:
            print "Querying GI for recommendations"
            recommendations = get_recommendations(username)
	    curr_time = time.time()
            for person in recommendations:
		#Mimick an 'insert or update' using the integrity exception
		try:
                    g.db.execute("INSERT INTO users (username, info, update_time) VALUES (?,?,?);", (person.get('user_name'), str(person), curr_time))
		except sqlite3.IntegrityError, m:
		    g.db.execute("UPDATE users SET info=?, update_time=? WHERE username=?", (str(person), curr_time, person.get('user_name')))
		try:
                    g.db.execute("INSERT INTO recommendations (yourself, recommendation, update_time) VALUES (?, ?, ?);", (username, person.get('user_name'), curr_time))
		except sqlite3.IntegrityError, m:
		    g.db.execute("UPDATE recommendations SET update_time=? WHERE yourself=? AND recommendation=?", (curr_time, username, person.get('user_name')))
            g.db.commit()
        except urllib2.HTTPError:
            return render_template('error.html', message="Sorry, our system is currently down. Try again later.")
    #remove people that are None
    recommendations = [person for person in recommendations if person]
    recommendations = util.sort_people_by_dist(yourself, recommendations)

    curs = g.db.execute("SELECT recommendation FROM recommendations WHERE has_met=? AND yourself=?", (True, username))
    already_met = [res[0] for res in curs.fetchall()]
    print "already met:", already_met

    print "Size of recs list before filtering:", len(recommendations)
    #Filter out yourself and people in your group and people you've already met and more than 3 days since last seen
    recommendations = [person for person in recommendations if person.get('user_name') != username and not intersect(yourself.get('affiliation', ''), person.get('affiliation', '')) and person.get('user_name') not in already_met and not ancient(person.get('last_time'))]
    print "Size of recs list after filtering:", len(recommendations)
    print "recommendations after filtering:", recommendations
    return recommendations

def retrieve_sponsor_recs(username, yourself):
    #Get sponsor recommendations  
    curs = g.db.execute("SELECT rec.username, rec.info, rec.update_time, rec.linkedin_id, sponsor_recs.update_time"\
        +" FROM users AS yourself, users AS rec, sponsor_recs"\
        +" WHERE yourself.username = ? AND sponsor_recs.yourself = yourself.username AND sponsor_recs.sponsor_rec = rec.username;", (username,))
    result = curs.fetchall()
    print "Result of querying db for sponsor_recs:", result
    use_cache = len(result) > 0
    curr_time = time.time()
    for res in result:
        if not (res and res[1] and time.time()-res[4] < REC_CACHE_TIME):
            use_cache = False
    if use_cache:
        print "Using cache for sponsor_recs"
        sponsor_recs = [eval(person[1]) for person in result]
    else:
        try:
            print "Querying GI for sponsor_recs"
            sponsor_recs = get_sponsor_recs(username)
            for person in sponsor_recs:
		try:
                    g.db.execute("INSERT INTO users (username, info, update_time) VALUES (?,?,?);", (person.get('user_name'), str(person), curr_time))
                except sqlite3.IntegrityError, m:
                    g.db.execute("UPDATE users SET info=?, update_time=? WHERE username=?", (str(person), curr_time, person.get('user_name')))
                try:                    
		    g.db.execute("INSERT INTO sponsor_recs (yourself, sponsor_rec, update_time) VALUES (?, ?, ?);", (username, person.get('user_name'), curr_time))
                except sqlite3.IntegrityError, m:
                    g.db.execute("UPDATE sponsor_recs SET update_time=? WHERE yourself=? AND sponsor_rec=?", (curr_time, username, person.get('user_name')))

            g.db.commit()
        except urllib2.HTTPError:
            return render_template('error.html', message="Sorry, our system is currently down. Try again later.")

    sponsor_recs = [person for person in sponsor_recs if person]
    sponsor_recs = util.sort_people_by_dist(yourself, sponsor_recs)

    curs = g.db.execute("SELECT sponsor_rec FROM sponsor_recs WHERE has_met=?AND yourself=?", (True, username))
    already_met = [res[0] for res in curs.fetchall()]
    print "already met:", already_met

    print "Size of sponsor_recs before filtering:", len(sponsor_recs)
    #Filter out yourself and people in your group and people you've already met and more than 3 days since last seen
    sponsor_recs = [person for person in sponsor_recs if person.get('user_name') != username and yourself.get('company_id') !=  person.get('company_id') and person.get('user_name') not in already_met and not ancient(person.get('last_time'))]
    print "Size of sponsor_recs after filtering:", len(sponsor_recs)
    print "sponsor_recs after filtering:", sponsor_recs
    return sponsor_recs

@app.route('/logout')
def logout():
    # remove the username from the session if its there

    session.pop('my_webcode', None)
    session.clear()    
    resp = make_response( redirect("http://qr.media.mit.edu/logout") )
#    return redirect("http://qr.media.mit.edu/logout?next=http://http://connectme.csc.media.mit.edu:3000/")
    resp.set_cookie('username', None) 
    resp.set_cookie('web_code', None)
    return resp



@app.route('/recommends', methods=['GET'])
def recommend_form_response():
#    print "called!", recs_cache
    username = request.cookies.get('username')
    if username:
        return redirect(url_for('recommend_for_user', username=username))
    else:
        return render_template('error.html', message="There has been a cookie error!")
    

@app.route('/recommends/<username>')
def recommend_for_user(username=None):
#    print "recommend!", request.cookies
    start = time.time()
    username = username.replace('@media.mit.edu', '')
    yourself = retrieve_yourself(username)
    recommendations = retrieve_recommendations(username, yourself)
    sponsor_recs = retrieve_sponsor_recs(username, yourself)
    print "recommend load time: ", time.time() - start

    return render_template('recommends.html', recommendations=recommendations, sponsor_recs=sponsor_recs, yourself=yourself, home_username=request.cookies.get('username')) 

    #resp = make_response( render_template('recommends.html', recommendations=recommendations,
    #                      sponsor_recs=sponsor_recs, yourself=yourself, concepts=concepts) )
    #resp.set_cookie('username', username)
    #return resp

@app.route('/charms', methods=['GET'])
def charms_form_response():
    username = request.cookies.get('username')
#    username = request.args.get('username')
    print "charm form response username", username
    if username:
	print "in username"
	return redirect(url_for('charms_for_user', username=username))
    else:
	return redirect(url_for('login'))

@app.route('/charms/<username>')
def charms_for_user(username):
    charms = get_charms(username) 
    charms.reverse()
    
    return render_template('charms.html', charms=charms, home_username=request.cookies.get('username'))

"""
@app.route('/recommend/topic/<topic>')
def recommend_for_topic(topic):
    vec = vec_for_phrase(topic)
    projects = get_related_projects(vec, 10)
    people = get_related_people(vec, 10)
    
    user_info = [(name, get_user_info(name), weight)
                       for (name, weight) in people]
    recommendations = [(info, weight,
                        intersect_related_concepts([vec, make_user_vec(name),
                                                    make_user_vec(name)], 100))
                       for name, info, weight in user_info]
    rec_pairs = []

    for i in xrange(len(recommendations)/2):
        other = i+len(recommendations)/2
        rec_pairs.append((recommendations[i][0],
                          recommendations[other][0]))
    return render_template('rec_for_topic.html', topic=topic, projects=projects,
rec_pairs=rec_pairs)
"""
@app.route('/set_met', methods=['POST'])
def set_met():
    if request.method == 'POST':
        if 'username' in request.cookies:
            username = request.cookies['username'] 
        else:
	    print "user name not in cookies!"
	    return render_template('error', message="You are not logged in. Please log in and try again.")
        if 'username' in request.form:
	    met = request.form['username']
	    curs = g.db.execute("UPDATE recommendations SET has_met=? WHERE yourself=? AND recommendation=?", (True, username, met))
	    curs = g.db.execute("UPDATE sponsor_recs SET has_met=? WHERE yourself=? AND sponsor_rec=?", (True, username, met)) 
	    g.db.commit()
	    print "Set that", username, "has met", met
	resp = make_response( redirect(url_for('profile', username=username)) )
        resp.set_cookie('username', username)
        return resp

#if __name__ == '__main__':
#    if socket.gethostname() == 'achilles':
#        app.run(host='0.0.0.0', debug=True)
#    else:
#        app.run(debug=True)

if __name__ == "__main__":
#    import cProfile
#    cProfile.run('profile(havasi')
    app.run("0.0.0.0", debug=True)

