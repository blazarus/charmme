from csc import divisi2
import numpy as np
import json, luminoso2, time, urllib2
from divisi2 import DenseMatrix
from csc_utils.ordered_set import OrderedSet
from charm_exceptions import *

#model = luminoso2.load('pldb_2011_may')
model = luminoso2.load('hack_2011_oct/Model')
sponsormat = divisi2.load("sponsors.dmat")
doc_matrix = model.get_doc_matrix('pldb')
tag_matrix = model.get_tag_matrix()

tag_matrix = model.get_tag_matrix()
tag_matrix = DenseMatrix.concatenate(tag_matrix, sponsormat)

for i in xrange(doc_matrix.shape[0]):
    doc_matrix.row_labels[i] = doc_matrix.row_labels[i].replace('hack_2011_oct/Documents', 'PLDBDocs')
#    print doc_matrix.row_labels[i]

def get_related_sponsors(email, n=10):
    if not ('sponsor', email) in tag_matrix.row_labels:
	return []
    vec = tag_matrix.row_named(('sponsor', email))
    got = divisi2.dot(tag_matrix, vec)
    results = []
    for tag, weight in got.top_items(len(got)):
        key, value = tag
        if key == 'sponsor':
            results.append((value, weight))
        if len(results) >= n:
            break
    return results

def get_related_people(vec, n=10):
    got = model.tags_similar_to_vector(vec)
    results = []
    for tag, weight in got.top_items(n*10):
        key, value = tag
        if key == 'person':
            results.append((value, weight))
        if len(results) >= n:
            break
    return results

def get_related_concepts(vec, n=10):
    got = model.domain_terms_similar_to_vector(vec)
    return best_phrases(got, n)

def best_phrases(simvec, n=10):
    filtered = simvec.top_items(n*4)
    favor_phrases = [(key, value*(len(key.split()))) for (key, value) in filtered]
    favor_phrases.sort(key=lambda item: -item[1])
    return favor_phrases[:n]

def intersect_related_concepts(categories, user_domains, n=10):
    if not isinstance(categories, list):
        categories = [categories]
    start = time.time() 
    prod = np.maximum(1e-6, model.domain_terms_similar_to_vector(categories[0]).top_items(10))
    print "irc:", time.time() - start
    return model.domain_terms_similar_to_vector(categories[0]).top_items(n)
#    mid = time.time()    
#    # Multiply together all non-negative concept values
#    for category in categories[1:]:
#        got = np.maximum(1e-6, model.domain_terms_similar_to_vector(category))
#        prod = divisi2.multiply(prod, got)
#    print "irc: start", time.time() - start
#    print "irc: mid", time.time() - mid
#    return best_phrases(prod, n)

# random text fragments Catherine found to put in for Joi before he's in the
# PLDB
JOI = """
technology, Japan,
Digital Garage, creative commons, the Lab helped to create a digital
revolution -- a revolution that is now over. We are a digital culture ... impact will be global, social, economic and
political -- Joi's world, music sharing, twitter, communication, world of
warcraft, middle east, computer graphics
"""

def make_user_vec(user):
    if user == 'joi':
        return vec_for_phrase(JOI)
    if '@' in user:
	return tag_matrix.row_named(('sponsor', user))
    return tag_matrix.row_named(('person', user))

def vec_for_phrase(phrase):
    return model.vector_from_text(phrase)

def get_doc_info(docid):
    doc = model.database.get_document(docid)
    tags = model.get_document_tags(docid)
    if len(doc.name) >= 40:
        name = doc.name+'...'
    else:
        name = doc.name
    people = []
    for key, value in tags:
        if key == u'person':
            people.append(value)
    return dict(name=name, people=people)

def get_related_projects(vec, n=10):
    top = model.docs_similar_to_vector(vec, 'pldb').top_items(n)
    return [(get_doc_info(doc), weight)
            for (doc, weight) in top]

def make_documents_vec(docs):
    from operator import __add__
    #print "docs is", docs
    #print "doc_matrix row labels", doc_matrix.row_labels
    vecs = [doc_matrix.row_named(doc) for doc in docs if doc in doc_matrix.row_labels]
    #print "vecs is", vecs
    if not vecs:
	raise InactiveCharmsException
    return reduce(__add__, vecs)
