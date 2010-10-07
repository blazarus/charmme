from flask import Flask, render_template, request, redirect, url_for, flash
from fromcharms import sponsor_rec, AntiSocialException, NotYourEmailException
import json
import urllib, urllib2
import socket
app = Flask(__name__)
app.secret_key = "NbNn4fpyT+pNKOL2gEKqo/dUvId7WzKc"
from use_lumie_study import get_related_people, get_related_concepts, intersect_related_concepts

@app.route('/')
def front_page():
    return render_template('start.html')

def get_user_info(username):
    if '@' in username:
        # handle sponsors:
        info = {
            'username': username,
            'name': username,
            'picture_url': "http://pldb.media.mit.edu/face/nobody",
            'known': False,
        }
        return info
    username = urllib.quote(username)
    try:
        url = "http://data.media.mit.edu/people/json/?filter=(cn=%s)" % username
        data = json.loads(urllib2.urlopen(url).read().decode('latin1'))
        data[0]['name'] # test to make sure it exists
        info = data[0]
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
    return info

def intersect(list1, list2):
    if isinstance(list1, basestring): list1 = list1.split(', ')
    if isinstance(list2, basestring): list2 = list2.split(', ')
    return set(list1) & set(list2)

def list_concepts(concept_list):
    return ', '.join(x[0] for x in concept_list if x[1] > 0)


@app.route('/recommend', methods=['GET'])
def recommend_form_response():
    username = request.args.get('username')
    if username:
        return redirect(url_for('recommend_for_user', username=username))
    if not username:
        return redirect(url_for('front_page'))

@app.route('/recommend/<username>')
def recommend_for_user(username=None):
    username = username.replace('@media.mit.edu', '')
    user_category = ['#person:'+username]
    if '@' in username:
        try:
            rec_items = sponsor_rec(username, 40)
        except AntiSocialException:
            flash(u"You don't have any charms yet. Go out and meet people!", 'error')
            return redirect(url_for('front_page'))
        except NotYourEmailException:
            flash(u"I don't recognize that e-mail address (%s). Please use the e-mail address that you registered for the event with." % username, 'error')
            return redirect(url_for('front_page'))
    else: rec_items = get_related_people("#person:%s" % username, 40)
    yourself = get_user_info(username)
    recommendations = [(get_user_info(name[8:]), weight, 
                        intersect_related_concepts(user_category + [name], 10))
                       for (name, weight) in rec_items
                       if name.startswith('#person:')
                       and name[8:] != username
                      ]
    recommendations = [item for item in recommendations
                       if item[0]['known']
                       and item[1] > 0.0
                       and not intersect(item[0]['affiliation'], yourself['affiliation'])
                      ][:10]
    if not recommendations:
        flash(u"Sorry, %s, I don't know who you are." % username, 'error')
        return redirect(url_for('front_page'))
    for rec in recommendations:
        rec[0]['topics'] = list_concepts(rec[2])
    rec_pairs = []
    for i in xrange(len(recommendations)/2):
        other = i+len(recommendations)/2
        rec_pairs.append((recommendations[i][0],
                          recommendations[other][0]))

    concept_list = get_related_concepts(user_category)
    concepts = list_concepts(concept_list)
    return render_template('people.html', recommendations=recommendations,
                          rec_pairs=rec_pairs, yourself=yourself, concepts=concepts)

if __name__ == '__main__':
    if socket.gethostname() == 'achilles':
        app.run(host='0.0.0.0')
    else:
        app.run(debug=True)

