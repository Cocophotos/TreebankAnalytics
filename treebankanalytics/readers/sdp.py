import os, re, sys

import treebankanalytics.graphs.Graph as G
from treebankanalytics.readers import utils

__all__ = ['sdp_reader']

def sdp_reader(fileo):
    kept_id = None
    numsent = 1
    predicates = []
    edges = {}
    graph = G.Graph()
    first = True

    with fileo:
        for i, line in enumerate(fileo):
            line = line.strip()
            if first:
                utils.add_root_node(graph)
                first = False

            if line == '':
                numsent += 1
                kept_id = None
                first = True

                for out_node in edges:
                    for predidx, label in enumerate(edges[out_node]):
                        if label == '_':
                            continue
                        edge = utils.create_edge(predicates[predidx], label, out_node)
                        if edge is not None:
                            graph.add_edge(edge)

                yield graph
                graph = G.Graph()
                predicates = []
                edges      = {}
                continue

            if utils.is_comment(line):
                kept_id = line[1:]
                continue

            items = line.split('\t')
            tid, token, lemma, pos, top, pred = items[:6]
            tid = int(tid)

            node = utils.create_node(tid, token, lemma, pos, pos, '_')
            edges[tid] = items[6:]

            top = True if top == '+' else False
            pred = True if pred == '+' else False
            if pred:
                predicates.append(tid)
            if top:
                utils.add_root_node(graph)

            if node.index() == 1 and kept_id is None:
                kept_id = "2%i" % numsent
            utils.add_id_to_features(kept_id, node)
            graph.add_node(node)
