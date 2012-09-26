import datetime, time
from operator import itemgetter, attrgetter

def distance(x1, x2):
    if x1 == None or x2 == None or x1.lower().startswith('location not found') or x2.lower().startswith('location not found'):
	print "One of the locations was not available"
	return 10000

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
    try:
        x1_fl = int(x1[4])
        x2_fl = int(x2[4])
    except:
	return 10000

    score = 0

    if x1_bldg != x2_bldg:
        score += 10

    score += abs(x1_fl - x2_fl)
#    print "vjw: score", score, "from ", x1
    return score

def sort_people_by_dist(yourself, people):
    for person in people:
	if yourself.get('last_loc') == None or person.get('last_loc') == None:
	    person['distance'] = 10000 #just make it a big number so its gets sorted to the bottom
        else:
            person['distance'] = distance(yourself.get('last_loc').get('readerid'), person.get('last_loc').get('readerid'))
    #make weight negative to get correct sort order
    sorted_list = sorted(people, key=lambda d: (d.get('distance'), -1*d.get('weight')))

    print "sorted list of people by distance to yourself:"
    for person in sorted_list:
	print "person", person.get('user_name'), "distance", person.get('distance'), "weight", person.get('weight')

    return sorted_list

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

