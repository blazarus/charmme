from csc import divisi2
import numpy as np
import json

docs = divisi2.load('PLDBStudy/Results/documents.smat')
proj = divisi2.load('PLDBStudy/Results/projections.dmat')
assoc = divisi2.load('PLDBStudy/Results/spectral.rmat')
stats = json.load(open('PLDBStudy/Results/stats.json'))

#terms = stats['terms']
terms = {}
for term in proj.row_labels:
    if not term.startswith('#'):
        terms[term] = term

# blacklist
#del terms['open mind common']   # turns into "Open Mind Commons", an obsolete project
#del terms['everyone room']      # "everyone in the room" - not a useful topic
#del terms['dynamic way']        # too vague
#del terms['beyond']             # not actually a noun
#del terms['use']                # how does this keep coming back?!
#del terms['approach']           # too vague
#del terms['collect hundred']    # not actually a noun phrase
#del terms['hundred']            # it's just a number
#del terms['thousand']           # it's just a number
#del terms['hundred thousand']   # it's just a number
#del terms['korean']             # too associated with common sense
#del terms['exploit']            # not actually a noun
#del terms['develop']            # not actually a noun
#del terms['new']                # not actually a noun
#del terms['various way']        # too vague

project_indices = [i for i in xrange(assoc.shape[0]) if assoc.row_label(i).endswith('.txt')]
people_indices = [i for i in xrange(assoc.shape[0]) if assoc.row_label(i).startswith('#')]
concept_indices = [i for i in xrange(assoc.shape[0]) if not assoc.row_label(i).startswith('#') and not assoc.row_label(i).endswith('.txt')]
concept_weights = docs.col_op(np.sum)[concept_indices]
means = np.asarray(assoc[:, concept_indices].to_dense()).mean(axis=0)

canonicals_text = {'Architecture and Design': ['architecture', 'build', 'design'],
              'Art and Technology': ['art', 'draw', 'color', 'sculpt', 'create'],
              'Artificial Intelligence': ['artificial intelligence'],
              'Banking': ['account', 'bank', 'money'],
              'Bioengineering': ['biomimetic', 'bioengineer'],
              'Cognition': ['thought', 'metacognition', '#person:dkroy', 'memory'],
              'Consumer Electronics':['tv', 'electronic', 'device'],
              'Decision Making, Influencing Behavior': ['decision', 'collaboration', 'influence', 'behavior', 'choice'],
              'Developing Countries':['develop', 'country', 'africa', 'help', 'world'],
              'Disability': ['deaf', 'blind', 'amputee', 'disability', 'aid'],
              'Economy and Technology': ['economic', 'commerce', 'e commerce', 'ecommerce', 'e-commerce', 'market', 'economy', 'vendor'],
              'Energy and Environment': ['energy', 'sustainable', 'environment'],
              'Entertainment': ['entertainment'],
              'Global Technologies': ['global', 'world'],
              'Health, Medicine': ['medicine', 'doctor', 'health'],
              'Humans & Machines': ['human', 'machine'],
              'Kids and Technology': ['child', 'young', 'play'],
              'Learning and Education': ['learn', 'educate'],
              'Mobility': ['mobility'],
              'Music': ['music'],
              'Politics and Technology': ['political'],
              'Privacy': ['privacy'],
              'Robotics': ['robotic', 'robot'],
              'Scaling and Networks':['network', 'scale'],
              'Social Interaction, Sharing, Social Networks': ['social interaction', 'social network', 'share'],
              'Storytelling': ['tell story', 'story tell', 'storytell'],
              'Transportation': ['train', 'car', 'vehicle', 'transport'],
              'Urban Environment': ['urban', 'city'],
              'Wearable': ['wearable'],
              'Wireless': ['wireless'],
              'Mobile Device': ['cell phone', 'mobile', 'mobile device']} 

canonicals = {}
for key, value in canonicals_text.items():
    canonicals[key] = divisi2.SparseVector.from_counts(value)
#print 'loaded'

def get_related_all(terms, n=10):
    if not isinstance(terms, list): terms = [terms]
    cat = divisi2.SparseVector.from_counts(terms)
    got = assoc.right_category(cat).top_items(n)
    return [(item[0], item[1]) for item in got]

def get_related_projects(terms, n=10):
    if not isinstance(terms, list): terms = [terms]
    cat = divisi2.SparseVector.from_counts(terms)
    got = assoc.right_category(cat)[project_indices].top_items(n)
    return [(int(item[0][:-4]), item[1]) for item in got]

def get_related_people(terms, n=10):
    if not isinstance(terms, list): terms = [terms]
    cat = divisi2.SparseVector.from_counts(terms)
    got = assoc.right_category(cat)[people_indices].top_items(n)
    return got

def get_related_concepts(cat, n=10):
    got = assoc.right_category(cat)[concept_indices].top_items(n)

    # Adjust order to favor multi-word concepts
    adjusted = []
    for concept, value in got:
        adjusted.append((concept, value*(3+len(concept.split()))))
    return sorted(adjusted, key=lambda x: -x[1])

def intersect_related_concepts(categories, n=10):
    if not isinstance(categories, list): categories = [categories]
    prod = np.maximum(1e-6, assoc.right_category(categories[0]))[concept_indices] - means
    
    # Multiply together all non-negative concept values
    for category in categories[1:]:
        got = np.maximum(1e-6, assoc.right_category(category))[concept_indices]
        prod = divisi2.multiply(prod, got-means)
    got2 = prod.top_items(n)
    
    # Adjust order to favor multi-word concepts
    adjusted = []
    for concept, value in got2:
        adjusted.append((concept, value*(3+len(concept.split()))))
    return sorted(adjusted, key=lambda x: -x[1])

def get_best_match(project, n=10):
    project = str(project) + '.txt'
    results = {}
    proj = assoc.row_named(project)
    for area,adhoc in canonicals.items():
        match = divisi2.aligned_matrix_multiply(proj.hat(),adhoc.hat())
        results[area] = match
    best = sorted([(value, key) for (key, value) in results.items()])[-5:][::-1]
    return [(x[1], x[0]) for x in best]
        
def make_user_category(usertag):
    return docs.col_named(usertag)

