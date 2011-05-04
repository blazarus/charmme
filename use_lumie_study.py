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
        
def make_user_vec(user):
    return tag_matrix.row_named(('person', user))

def make_documents_vec(docs):
    from operator import __add__
    vecs = [doc_matrix.row_named(doc) for doc in docs if doc in doc_matrix.row_labels]
    return reduce(__add__, vecs)
