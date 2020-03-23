import os, re, sys

import treebankanalytics.graphs.Graph as G
from treebankanalytics.readers import utils

__all__ = ['sequoia_reader']

def sequoia_reader(fileo, lower = False):
    kept_id = None
    graph   = G.Graph()
    first   = True

    with fileo:
        for i, line in enumerate(fileo):
            line = line.strip()
            if first:
                utils.add_root_node(graph)
                first = False

            if line == "":
                #Reset all and produce graph
                kept_id = None
                first = True
                yield graph
                graph = G.Graph()
                continue

            if utils.is_comment(line):
                kept_id = line[1:]
                continue

            items = re.split('\t', line)
            node = utils.create_node(*items[:6])
            utils.add_id_to_features(kept_id, node)
            if len(items) > 8:
                utils.handle_extra_columns(node, items[8:])
            graph.add_node(node)

            dep = items[0]
            if len(items) > 7:
                for head, label in zip(items[6].split('|'), items[7].split('|')):
                    if lower:
                        label = label.lower()
                    edge = utils.create_edge(head, label, dep)
                    if edge is not None:
                        graph.add_edge(edge)
