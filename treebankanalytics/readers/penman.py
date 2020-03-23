import os, re, sys
import treebankanalytics.graphs.Graph as G
from typing import List, Set
from treebankanalytics.readers import utils

__all__ = ['penman_reader']

def denormalize_brackets(s: str) -> str:
    return s.replace("-LRB-", "(").replace("-RRB-" ")")

def denormalize_dots(s: str) -> str:
    return s.replace("-DDOTS-", ":")

def parse(actions: List[str], nodes: List[G.Node], lower: bool) -> G.Graph:
    graph = G.Graph()
    utils.add_root_node(graph)
    for n in nodes:
        graph.add_node(n)

    currParent = None
    currLabel = None
    for i, c in enumerate(actions):
        #print('action:', c)
        if c == '(':
            continue
        elif c == ')':
            currParent = None
            currLabel = None
        elif c.startswith(':'):
            label = denormalize_dots(c[1:])
            currLabel = label
        elif c == '</s>':
            continue
        else:
            node_idx = int(c.split('_')[0])
            if currParent is not None:
                try:
                    n = graph.node(node_idx)
                    e = utils.create_edge(currParent, currLabel, node_idx)
                    graph.add_edge(e)
                    #print('edge:', currParent, currLabel, node_idx) 
                    # Parent needs to be changed
                    if i > 0 and actions[i-1] == '(':
                        currParent = node_idx
                except AttributeError:
                    pass
            else:
                try:
                    n = graph.node(node_idx)
                    if i > 0 and actions[i-1] == ')':
                        continue # This is an empty node
                    currParent = node_idx
                except AttributeError:
                    pass
    return graph

def penman_reader(fileo, lower = False):
    with fileo as stream:
        actions = []
        nodes = []
        kept_id = None
        for line in stream:
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
