import json
import urllib2

info_cache = {}
def get_proj_info(proj_id):
    if proj_id in info_cache: return info_cache[proj_id]

    http_stream = urllib2.urlopen('http://data.media.mit.edu/pldb/json?query=project.id=%d' % proj_id)
    data = json.load(http_stream)
    info_cache[proj_id] = data
    return data

def get_proj_name(proj_id):
    info = get_proj_info(proj_id)
    return info['projectname'], info['researchgroup']
