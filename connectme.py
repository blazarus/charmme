from flask import Flask, render_template
import json
import urllib, urllib2
app = Flask(__name__)

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

@app.route('/recommend/<username>')
def recommend_for_user(username):
    rec_items = get_related_people("#person:%s" % username, 20)
    recommendations = [(get_user_info(name[8:]), weight)
                       for (name, weight) in rec_items
                       if name.startswith('#person:')
                       and name[8:] != username
                      ]
    recommendations = [item for item in recommendations if item[0]['known']][:10]
    return render_template('people.html', recommendations=recommendations)

if __name__ == '__main__':
    app.run(debug=True)

