import os, re, sys

import treebankanalytics.graphs.Graph as G
from treebankanalytics.readers import utils


__all__ = ['sagae_reader']

def sagae_reader(fileo):
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

            if len(items) > 6:
                head, label = items[6:8]
                dep         = items[0]
                edge = utils.create_edge(head, label, dep)
                if edge is not None:
                    graph.add_edge(edge)
