from flask import Flask, render_template, request, redirect, url_for, flash
from fromcharms import sponsor_category, sponsor_rec, AntiSocialException, NotYourEmailException
import json
import urllib, urllib2
import socket
app = Flask(__name__)
app.secret_key = "NbNn4fpyT+pNKOL2gEKqo/dUvId7WzKc"
from use_lumie_study import get_related_people, get_related_concepts, intersect_related_concepts, terms, make_user_category

user_info_cache = {}

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
    if username in user_info_cache: return user_info_cache[username]
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
    user_info_cache[username] = info
    return info

def intersect(list1, list2):
    if isinstance(list1, basestring): list1 = list1.split(', ')
    if isinstance(list2, basestring): list2 = list2.split(', ')
    return set(list1) & set(list2)

def list_phrases(concept_list, terms, n=8):
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
        if weight > 0:
            expanded = terms.get(concept)
            if expanded:
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

def user_tag(username):
    return '#person:'+username

@app.route('/recommend', methods=['GET'])
def recommend_form_response():
    username = request.args.get('username')
    if username:
        return redirect(url_for('recommend_for_user', username=username))
    else:
        return redirect(url_for('front_page'))

@app.route('/recommend/<username>')
def recommend_for_user(username=None):
    username = username.replace('@media.mit.edu', '')
    if '@' in username:
        username = username.replace('@test', '')
        try:
            rec_items = sponsor_rec(username, 40)
            user_category = sponsor_category(username)
        except AntiSocialException:
            flash(u"You don't have any charms yet. Go out and meet people!", 'error')
            return redirect(url_for('front_page'))
        except NotYourEmailException:
            flash(u"I don't recognize that e-mail address (%s). Please use the e-mail address that you registered for the event with." % username, 'error')
            return redirect(url_for('front_page'))
    else:
        rec_items = get_related_people(user_tag(username), 40)
        try:
            user_category = make_user_category(user_tag(username))
        except KeyError:
            flash(u"Sorry, %s, I don't know who you are." % username, 'error')
            return redirect(url_for('front_page'))

    yourself = get_user_info(username)
    user_info = [(name[8:], get_user_info(name[8:]), weight)
                       for (name, weight) in rec_items
                       if name.startswith('#person:')
                       and name[8:] != username]
    not_same_group = [(name, info, weight) for name, info, weight in user_info
                       if info['known']
                       and weight > 0.0
                       and not intersect(info['affiliation'], yourself['affiliation'])]
    recommendations = [(info, weight,
                        intersect_related_concepts([user_category, make_user_category(user_tag(name))], 100))
                       for name, info, weight in not_same_group[:10]]
    if not recommendations:
        flash(u"Sorry, %s, I don't know who you are." % username, 'error')
        return redirect(url_for('front_page'))
    for rec in recommendations:
        rec[0]['topics'] = list_phrases(rec[2], terms, 8)
    rec_pairs = []
    for i in xrange(len(recommendations)/2):
        other = i+len(recommendations)/2
        rec_pairs.append((recommendations[i][0],
                          recommendations[other][0]))

    concept_list = get_related_concepts(user_category, 100)
    concepts = list_phrases(concept_list, terms, 8)
    return render_template('people.html', recommendations=recommendations,
                          rec_pairs=rec_pairs, yourself=yourself, concepts=concepts)

if __name__ == '__main__':
    if socket.gethostname() == 'achilles':
        app.run(host='0.0.0.0')
    else:
        app.run(debug=True)

