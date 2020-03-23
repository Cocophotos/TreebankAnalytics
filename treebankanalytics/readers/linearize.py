import os, re, sys

import treebankanalytics.graphs.Graph as G
from treebankanalytics.readers import utils
from typing import List

__all__ = ['linearize_reader']

def parse(actions: List[str], nodes: List[G.Node], lower: bool) -> G.Graph:
    graph = G.Graph()
    utils.add_root_node(graph)
    for n in nodes:
        graph.add_node(n)

    # For pass actions
    delta = []
    # This is the buffer
    beta = list(reversed(graph.nodes()))
    # This is the stack
    sigma = [beta.pop()] # Start with the root node

    for a in actions:
        if a.upper() == 'NS':
            sigma = sigma + list(reversed(delta))
            if len(beta) > 0:
                sigma.append(beta.pop())
            delta = []
        elif a.upper() == 'NR':
            if len(sigma) > 0:
                sigma.pop()
        elif a.upper() == 'NP':
            if len(sigma) > 0:
                delta.append(sigma[0])
                sigma.pop()
        elif a.upper().startswith('LR'):
            if len(sigma) == 0 or len(beta) == 0:
                continue
            
            label = a.upper()[3:-1]
            if lower:
                label = label.lower()
            e = utils.create_edge(beta[-1].index(), label, sigma[-1].index())
            
            graph.add_edge(e)
            sigma.pop()
        elif a.upper().startswith('LP'):
            if len(sigma) == 0 or len(beta) == 0:
                continue
            
            label = a.upper()[3:-1]
            if lower:
                label = label.lower()
            e = utils.create_edge(beta[-1].index(), label, sigma[-1].index())
            graph.add_edge(e)
            
            delta.append(sigma.pop())
        elif a.upper().startswith('RS'):
            if len(sigma) == 0 or len(beta) == 0:
                continue
            
            label = a.upper()[3:-1]
            if lower:
                label = label.lower()
            e = utils.create_edge(sigma[-1].index(), label, beta[-1].index())
            graph.add_edge(e)
            
            sigma = sigma + list(reversed(delta))
            delta = []
            sigma.append(beta.pop())
        elif a.upper().startswith('RP'):
            if len(sigma) == 0 or len(beta) == 0:
                continue
            
            label = a.upper()[3:-1]
            if lower:
                label = label.lower()
            e = utils.create_edge(sigma[-1].index(), label, beta[-1].index())
            graph.add_edge(e)
            
            delta.append(sigma.pop())
    return graph

def linearize_reader(fileo, lower = False):
    with fileo:
        actions = []
        nodes = []

        for i, line in enumerate(fileo):
            line = line.strip()
            if line == "":
                graph = parse(actions, nodes, lower)
                yield graph
                #Reset all and produce graph
                actions = []
                nodes = []
                kept_id = None
                continue

            if utils.is_comment(line):
                if utils.is_comment_with_id(line):
                    kept_id = line[1:]
                    continue
                else:
                    actions = line[1:].split(' ')
                    continue

            items = re.split('\t', line)
            node = utils.create_node(*items[:6])
            utils.add_id_to_features(kept_id, node)
            nodes.append(node)
