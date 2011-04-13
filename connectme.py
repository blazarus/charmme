from flask import Flask, render_template, request, redirect, url_for, flash
from fromcharms import sponsor_category, sponsor_rec, AntiSocialException, NotYourEmailException, charms_for_user
import json
import urllib, urllib2
import socket
import nltk
app = Flask(__name__)
app.secret_key = "NbNn4fpyT+pNKOL2gEKqo/dUvId7WzKc"
from use_lumie_study import get_related_people, get_related_concepts, intersect_related_concepts, model, make_user_vec

user_info_cache = {}

blacklist = ['mind common', 'everyone room', 'dynamic way', 'beyond', 'use',
             'approach', 'collect hundred', 'hundred', 'thousand',
             'hundred thousand', 'korean', 'exploit', 'develop', 'new',
             'various way', 'date everyone', 'enable', 'leverage', 'tool use',
             'various', 'project explores']

@app.route('/')
def front_page():
    return render_template('start.html')

def get_user_info(username):
    if username in user_info_cache: return user_info_cache[username]
    if '@' in username:
        try:
            data = json.load(urllib2.urlopen('http://tagnet.media.mit.edu/users?user_name=%s&capability=profile' % urllib.quote(username)))['profile']
            info = dict(
                username=username,
                name=data['name'],
                picture_url=data['picture_url'],
                affiliation=', '.join(data['affiliation']),
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
                }
            return info
    try:
        url = "http://data.media.mit.edu/people/json/?filter=(cn=%s)" % urllib.quote(username)
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
            expanded = model.database.get_term_text(concept)
            if expanded and is_noun_phrase(expanded):
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
    user_charms = []
    if '@' in username:
        username = username.replace('@test', '@media.mit.edu')
        try:
            user_charms = charms_for_user(username)
            user_vec = sponsor_category(username)
        except AntiSocialException:
            flash(u"You don't have any charms yet. Go out and meet people!", 'error')
            return redirect(url_for('front_page'))
        except NotYourEmailException:
            flash(u"I don't recognize that e-mail address (%s). Please use the e-mail address that you registered for the event with." % username, 'error')
            return redirect(url_for('front_page'))
    else:
        try:
            user_vec = make_user_vec(username)
        except KeyError:
            flash(u"Sorry, %s, I don't know who you are." % username, 'error')
            return redirect(url_for('front_page'))

    rec_items = get_related_people(user_vec, 40)
    yourself = get_user_info(username)
    yourself['num_charms'] = len(user_charms)
    yourself['charms'] = user_charms
    user_info = [(name, get_user_info(name), weight)
                       for (name, weight) in rec_items
                       if name != username]
    not_same_group = [(name, info, weight) for name, info, weight in user_info
                       if info['known']
                       and weight > 0.0
                       and not intersect(info['affiliation'], yourself.get('affiliation', ''))]
    recommendations = [(info, weight,
                        intersect_related_concepts([user_vec, make_user_vec(name), make_user_vec(name)], 100))
                       for name, info, weight in not_same_group[:10]]
    if not recommendations:
        #assert False
        flash(u"Sorry, %s, I don't know who you are." % username, 'error')
        return redirect(url_for('front_page'))
    for rec in recommendations:
        rec[0]['topics'] = list_phrases(rec[2], 8)
    rec_pairs = []
    for i in xrange(len(recommendations)/2):
        other = i+len(recommendations)/2
        rec_pairs.append((recommendations[i][0],
                          recommendations[other][0]))

    concept_list = get_related_concepts(user_vec, 100)
    concepts = list_phrases(concept_list, 8)
    return render_template('people.html', recommendations=recommendations,
                          rec_pairs=rec_pairs, yourself=yourself, concepts=concepts)

if __name__ == '__main__':
    if socket.gethostname() == 'achilles':
        app.run(host='0.0.0.0', debug=True)
    else:
        app.run(debug=True)

