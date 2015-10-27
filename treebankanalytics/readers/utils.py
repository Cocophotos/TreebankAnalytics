import os, re, sys
import treebankanalytics.graphs.Graph as G

__all__ = ['add_root_node', 'is_comment', 'create_node', 'create_edge', 'add_id_to_features', 'normalize_features']

def add_root_node(graph):
    top_node = G.Node(0, {'token':'_top_', 'lemma':'_top_', 'cpos':'_', 'pos':'_', 'features':'_'})
    graph.add_node(top_node)

def normalize_features(features):
    if isinstance(features, str):
        if features == '_':
            return {}
        else:
            return dict([item.split('=') for item in features.split('|') if item != "_"])
    else:
        return '|'.join(["{0}={1}".format(k, features[k]) for k in features])

def is_comment(line):
    return line.startswith('#')

def create_node(id, token, lemma, cpos, pos, features):
    args = {
        'token': token,
        'lemma': lemma,
        'cpos': cpos,
        'pos': pos,
        'features': normalize_features(features)
    }
    node = G.Node(int(id), args)
    return node

def create_edge(head, label, dep):
    if head == "-1" or head == "":
        return None
    return G.Edge(int(head), int(dep), {'label': label})

def add_id_to_features(id, node):
    if id is None:
        return

    if node.index() == 1:
        node['features']['sentid'] = id
