import os, re, sys

import treebankanalytics.graphs.Graph as G
from treebankanalytics.writers import utils

__all__ = ['tikz_writer']

def tikz_writer(graph, fileo):
    nodes = graph.nodes()[1:] #Remove root node from the list
    #\begin{dependency}
    #    \begin{deptext}[column sep=.5cm]
    #        My \& dog \& also \& likes \& eating \& sausage \\
    #        PRP\$ \& NN \& RB \&[.5cm] VBZ \& VBG \& NN \\
    #    \end{deptext}
    #    \deproot{4}{root}
    #    \depedge{2}{1}{poss}
    #    \depedge{4}{2}{nsubj}
    #    \depedge{4}{3}{advmod}
    #    \depedge{4}{5}{xcomp}
    #    \depedge{5}{6}{dobj}
    #\end{dependency}

    id, token, lemma, cpos, pos, features = utils.get_node(graph.nodes()[0])
    tokens = []
    poss = []
    tikzheads = []

    for n in nodes:
        #Get every information needed (features is a string formatted x=y|z=w)
        id, token, lemma, cpos, pos, features = utils.get_node(n)
        tokens.append(token);
        poss.append(pos);

        #Get every heads of n
        try:
            heads = graph.sources_of(n).values()
            done = False
            for e in heads:
                #Get head integer, label and dep integer (should be the same as n)
                head, label, _ = utils.get_edge(e)
                if head == 0:
                    tikzheads.append("\t\\deproot{%i}{%s}" % (id, label))
                else:
                    tikzheads.append("\t\\depedge{%i}{%s}" % (head, label))
                done = True
        except AttributeError:
            done = False

        if not done:
            tokens.append(token)
            poss.append(pos)

    print("\\begin{dependency}", file=fileo)
    print("\t\\begin{deptext}", file=fileo)
    print("\t\t%s \\\\" % " \\& ".join(tokens), file=fileo)
    print("\t\t%s \\\\" % " \\& ".join(poss), file=fileo)
    print("\t\\end{deptext}", file=fileo)
    print("\n".join(tikzheads), file=fileo)
    print("\\end{dependency}", file=fileo)
    print("", file=fileo)
