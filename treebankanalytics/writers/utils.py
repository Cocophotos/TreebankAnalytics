import os, re, sys
import treebankanalytics.graphs.Graph as G
from treebankanalytics.readers.utils import normalize_features
__all__ = ['get_node', 'get_edge', 'remove_id_from_features', 'get_sentence_id']

def get_sentence_id(graph):
    n1 = graph.nodes()[1]
    if 'features' in n1 and 'sentid' in n1['features']:
        return n1['features']['sentid']
    else:
        return None

def get_node(node):
    if 'features' not in node:
        features = '_'
    else:
        features = normalize_features(node['features'])
        if features == "": features = '_'

    return node.index(), node['token'], node['lemma'], node['cpos'], node['pos'], features

def get_edge(edge):
    return edge.source(), edge['label'], edge.target()

def remove_id_from_features(graph):
    n1 = graph.nodes()[1]
    if 'features' in n1 and 'sentid' in n1['features']:
        del n1['features']['sentid']
