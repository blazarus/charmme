from csc import divisi2
import numpy as np
import json
import luminoso2

model = luminoso2.load('pldb_luminoso2')
doc_matrix = model.get_doc_matrix('pldb')
tag_matrix = model.get_tag_matrix()


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
    return got.top_items(n)

def intersect_related_concepts(categories, n=10):
    if not isinstance(categories, list):
        categories = [categories]
    
    prod = np.maximum(1e-6, model.domain_terms_similar_to_vector(categories[0]))
    
    # Multiply together all non-negative concept values
    for category in categories[1:]:
        got = np.maximum(1e-6, model.domain_terms_similar_to_vector(category))
        prod = divisi2.multiply(prod, got)
    return prod.top_items(n)

# random text fragments Catherine found to put in for Joi before he's in the
# PLDB
JOI = """
learning, technology, innovation, Japan, help, Caucus was a groupware product
developed by Charles Roth, also helped start a computer graphics company, I
started writing a little and was on the masthead of Mondo 2000 and Wired
Magazine. (Although the only thing I ended up writing was one article and
nothing good enough to make it in Wired.)  We created a web joint venture with
an ad company, From Garage and called it Digital Garage, open source, learning,
creative commons, In the past 25 years, the Lab helped to create a digital
revolution -- a revolution that is now over. We are a digital culture. Today,
the 'media' in Media Lab include the widest range of innovations, from brain
sciences to the arts. Their impact will be global, social, economic and
political -- Joi's world, music sharing, twitter, open source, world of
warcraft, middle east, asia
"""

def make_user_vec(user):
    if user == 'joi':
        return vec_for_phrase(JOI)
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
    vecs = [doc_matrix.row_named(doc) for doc in docs if doc in doc_matrix.row_labels]
    return reduce(__add__, vecs)
