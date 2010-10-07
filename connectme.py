from flask import Flask, render_template, request, redirect, url_for, flash
from fromcharms import sponsor_rec, AntiSocialException, NotYourEmailException
import json
import urllib, urllib2
app = Flask(__name__)
app.secret_key = "NbNn4fpyT+pNKOL2gEKqo/dUvId7WzKc"
from use_lumie_study import get_related_people

@app.route('/')
def front_page():
    return render_template('start.html')

def get_user_info(username):
    username = urllib.quote(username)
    try:
        url = "http://data.media.mit.edu/people/json/?filter=(cn=%s)" % username
        data = json.loads(urllib2.urlopen(url).read().decode('latin1'))
        data[0]['name'] # test to make sure it exists
        info = data[0]
        info['mldirectory'] = "http://allegra.media.mit.edu/mldirectory.nsf/people/%s" % username
        info['known'] = True
        if isinstance(info['affiliation'], list):
            info['affiliation'] = ', '.join(info['affiliation'])
    except IndexError:
        info = {
            'username': username,
            'name': username,
            'picture_url': "http://pldb.media.mit.edu/face/%s" % username,
            'known': False
        }
    return info

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
    if '@' in username:
        try:
            rec_items = sponsor_rec(username, 20)
        except AntiSocialException:
            flash(u"You don't have any charms yet. Go out and meet people!", 'error')
            return redirect(url_for('front_page'))
        except NotYourEmailException:
            flash(u"I don't recognize that e-mail address. Please use the e-mail address that you registered for the event with.")
            return redirect(url_for('front_page'))
    else: rec_items = get_related_people("#person:%s" % username, 20)

    recommendations = [(get_user_info(name[8:]), weight)
                       for (name, weight) in rec_items
                       if name.startswith('#person:')
                       and name[8:] != username
                      ]
    recommendations = [item for item in recommendations if item[0]['known'] and item[1] > 0.0][:10]
    if not recommendations:
        flash(u"Sorry, I don't know who you are.", 'error')
        return redirect(url_for('front_page'))
    rec_pairs = []
    for i in xrange(len(recommendations)/2):
        rec_pairs.append((recommendations[i][0], recommendations[i+len(recommendations)/2][0]))
    return render_template('people.html', recommendations=recommendations,
                          rec_pairs=rec_pairs)

if __name__ == '__main__':
    app.run(debug=True)

