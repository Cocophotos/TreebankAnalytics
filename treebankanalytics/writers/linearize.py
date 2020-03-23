import os, re, sys
import treebankanalytics.graphs.Graph as G
from typing import List, Set
from treebankanalytics.writers import utils

__all__ = ['linearize_writer']

def has_edge(u: G.Node, v: G.Node, g: G.Graph) -> bool:
    """
    @param u First node
    @param v Second node
    @return True if an edge between u -> v exists 
    """
    try:
        g.edge(u.index(), v.index())
        return True
    except AttributeError:
        return False

def has_missing_edges(v: G.Node, g: G.Graph, edges: Set[G.Edge]):
    try:
        my_edges = g.edges_of(v.index())
        return len(set(my_edges) - edges) > 0
    except AttributeError:
        return False

def has_missing_edges_in_stack(v: G.Node, g: G.Graph, edges: Set[G.Edge], stack: List[G.Node]):
    my_edges = set()
    for u in stack[:-1]: # Do not consider the first node in stack
        try:
            e1 = g.edge(u.index(), v.index())
            my_edges.add(e1)
        except:
            pass
        
        try:
            e2 = g.edge(v.index(), u.index())
            my_edges.add(e2)
        except:
            pass
    return len(set(my_edges) - edges) > 0

def get_arc_label(u: G.Node, v: G.Node, g: G) -> str:
    """
    @param u The target node
    @param v The source node
    @return The label of the edge u -> v
    """
    try:
        e = g.edge(u.index(), v.index())
        _, label, _ = utils.get_edge(e)
        return label
    except AttributeError:
        return None

def linearize_writer(graph: G.Graph, fileo):
    #List-based graph parsing, taken from https://www.aaai.org/ocs/index.php/AAAI/AAAI18/paper/view/16549/16113

    # For pass actions
    delta = []
    # This is the buffer
    beta = list(reversed(graph.nodes()))
    # This is the stack
    sigma = [beta.pop()] # Start with the root node
    # This is the edge sets
    edges = set()
    
    actions = []
    while len(beta) > 0:
        s0 = -1 if len(sigma) == 0 else sigma[-1]
        b0 = -1 if len(beta) == 0 else beta[-1]
        
        if s0 != -1 and s0.index() > 0 and has_edge(b0, s0, graph):
            if not has_missing_edges(s0, graph, edges): 
                actions.append("LR(%s)" % get_arc_label(b0, s0, graph))
                edges.add(graph.edge(b0.index(), s0.index()))
                sigma.pop()
            else:
                actions.append("LP(%s)" % get_arc_label(b0, s0, graph))
                edges.add(graph.edge(b0.index(), s0.index()))
                delta.append(s0)
                sigma.pop()
        elif s0 != -1 and s0.index() > 0 and has_edge(s0, b0, graph):
            if not has_missing_edges_in_stack(b0, graph, edges, sigma):  #not has_other_child_in_stack(sigma, b0) and not has_other_head_in_stack(sigma, b0):
                actions.append("RS(%s)" % get_arc_label(s0, b0, graph))
                sigma = sigma + list(reversed(delta))
                delta = []
                sigma.append(b0)
                beta.pop()
                edges.add(graph.edge(s0.index(), b0.index()))
            else: #if s0.index() > 0
                actions.append("RP(%s)" % get_arc_label(s0, b0, graph))
                delta.append(s0)
                sigma.pop()
                edges.add(graph.edge(s0.index(), b0.index()))
        elif len(beta) > 0 and not has_missing_edges_in_stack(b0, graph, edges, sigma): 
            actions.append("NS")
            #actions.append("NS(%s)" % b0['token'])
            sigma = sigma + list(reversed(delta))
            delta = []
            sigma.append(b0)
            beta.pop()
        elif s0 != -1 and s0.index() > 0 and not has_missing_edges(s0, graph, edges):
            actions.append("NR")
            #actions.append("NR(%s)" % s0['token'])
            sigma.pop()
        elif s0 != -1 and s0.index() > 0:
            actions.append("NP")
            #actions.append("NP(%s)" % s0['token'])
            delta.append(s0)
            sigma.pop()
        else:
            actions.append("-E-")
            print("An error occurred when generating the gold actions", file=sys.stderr)
    print(" ".join(actions), file=fileo)
