import os, re, sys

import treebankanalytics.graphs.Graph as G
from treebankanalytics.writers import utils

__all__ = ['sagae_writer']

def sagae_writer(graph, fileo):
    nodes = graph.nodes()[1:] #Remove root node from the list
    for n in nodes:
        #Get every information needed (features is a string formatted x=y|z=w)
        id, token, lemma, cpos, pos, features = utils.get_node(n)
        extra = utils.handle_extra_columns(n)

        if isinstance(extra, list):
            extra = "\t".join(extra)

        #Get every heads of n
        try:
            heads = graph.sources_of(n).values()
            done = False
            for e in heads:
                #Get head integer, label and dep integer (should be the same as n)
                head, label, _ = utils.get_edge(e)
                if extra != "":
                    print("%i\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (id, token, lemma, cpos, pos, features, head, label, extra), file=fileo)
                else:
                    print("%i\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (id, token, lemma, cpos, pos, features, head, label), file=fileo)
                done = True
        except AttributeError:
            done = False

        if not done:
            if extra != "":
                print("%i\t%s\t%s\t%s\t%s\t%s\t-1\tNONE\t%s" % (id, token, lemma, cpos, pos, features, extra), file=fileo)
            else:
                print("%i\t%s\t%s\t%s\t%s\t%s" % (id, token, lemma, cpos, pos, features), file=fileo)
    print("", file=fileo)
