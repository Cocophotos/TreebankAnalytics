import os, re, sys
import treebankanalytics.graphs.Graph as G
from typing import List, Set
from treebankanalytics.writers import utils

__all__ = ['penman_writer']

def normalize_brackets(s: str) -> str:
    return s.replace("(", "-LRB-").replace(")", "-RRB-")

def normalize_dots(s: str) -> str:
    return s.replace(":", "-DDOTS-")

def penman_writer(graph: G.Graph, fileo):
    def dfs(u: G.Node, visited: Set[G.Node]):
        visited.add(u)
        children = []
        try: 
            children = graph.targets_of(u).values()
        except AttributeError:
            pass
            
        info = []

        if len(children) > 0:
            info = ["("]

        #info.append(normalize_brackets(u['token']))
        info.append(normalize_brackets("%s_%s" % (str(u.index()), u['pos'])))
        for e in children:
            _, label, tar_idx = utils.get_edge(e)
            v = graph.node(tar_idx)
            if v not in visited:
                info.append(":%s" % normalize_dots(label))
                info.append(dfs(v, visited))
            else:
                #info.append(":%s %s" % (normalize_dots(label), normalize_brackets(v['token'])))
                info.append(":%s %s_%s" % (normalize_dots(label), str(v.index()), normalize_brackets(v['pos'])))

        if len(children) > 0:
            info.append(")")
        return " ".join(info)


    visited = set()
    nodes = graph.nodes()
    penmans = []
    for n in nodes:
        if n in visited:
            continue
        penmans.append(dfs(n, visited))

    if len(penmans) > 1:
        print(" ".join(penmans))
    else:
        print(" ".join(penmans)[2:-2], file=fileo)
    

