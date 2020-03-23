import os, re, sys

import treebankanalytics.graphs.Graph as G
from treebankanalytics.readers import utils

__all__ = ['common_sdp_reader']

def common_sdp_reader(fileo, sdp_type = '2014', lower = False):
    kept_id = None
    numsent = 1
    predicates = []
    edges = {}
    graph = G.Graph()
    #first = True

    with fileo:
        for i, line in enumerate(fileo):
            line = line.strip()
            #if first:
            #    utils.add_root_node(graph)
            #    first = False

            if line == '':
                numsent += 1
                kept_id = None
                #first = True

                for out_node in edges:
                    for predidx, label in enumerate(edges[out_node]):
                        if label == '_':
                            continue
                        if lower:
                            label = label.lower()
                        edge = utils.create_edge(predicates[predidx], label, out_node)
                        if edge is not None:
                            graph.add_edge(edge)

                yield graph
                graph = G.Graph()
                predicates = []
                edges      = {}
                continue

            if utils.is_comment(line):
                if utils.is_comment_with_id(line):
                    kept_id = line[1:]
                continue

            items = line.split('\t')
            tid, token, lemma, pos, top, pred = items[:6]
            tid = int(tid)
            node = utils.create_node(tid, token, lemma, pos, pos, '_')
            if sdp_type == '2014':
                edges[tid] = items[6:]
            else:
                edges[tid] = items[7:] # skip frame

            top = True if top == '+' else False
            pred = True if pred == '+' else False
            if pred:
                predicates.append(tid)

            if node.index() == 1 and kept_id is None:
                kept_id = "2%i" % numsent
            utils.add_id_to_features(kept_id, node)
            graph.add_node(node)

            if top:
                utils.add_root_node(graph)
                graph.add_edge(utils.create_edge(0, 'root', 1))
