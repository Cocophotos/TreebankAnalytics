import codecs, os, re, sys, functools

from collections import defaultdict
from collections import OrderedDict

import argparse

__all__ = ['Graph', 'read_sagae', 'read_deepsequoia', 'print_graph', 'Node', 'Edge']

class ComparableMixin(object):
    """Mixin which implements rich comparison operators in terms of a single _compare_to() helper"""

    def _compare_to(self, other):
        """return keys to compare self to other.

        if self and other are comparable, this function
        should return ``(self key, other key)``.
        if they aren't, it should return ``None`` instead.
        """
        raise NotImplementedError("_compare_to() must be implemented by subclass")

    def __eq__(self, other):
        keys = self._compare_to(other)
        return keys[0] == keys[1] if keys else NotImplemented

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        keys = self._compare_to(other)
        return keys[0] < keys[1] if keys else NotImplemented

    def __le__(self, other):
        keys = self._compare_to(other)
        return keys[0] <= keys[1] if keys else NotImplemented

    def __gt__(self, other):
        keys = self._compare_to(other)
        return keys[0] > keys[1] if keys else NotImplemented

    def __ge__(self, other):
        keys = self._compare_to(other)
        return keys[0] >= keys[1] if keys else NotImplemented

class Node(ComparableMixin, object):
    def __init__(self, idx, features):
        self._idx = idx
        self._features = features

    def features(self):
        return self._features

    def index(self):
        return self._idx

    def __setitem__(self, k, v):
        self._features[k] = v

    def __getitem__(self, k):
        if k in self._features:
            return self._features[k]
        raise AttributeError

    def _compare_to(self, other):
        return (hash(self), hash(other))

    def __hash__(self):
        return self._idx

    def __contains__(self, item):
        if item in self._features:
            return True
        return False

class Edge(ComparableMixin, object):
    def __init__(self, source, target, features):
        self._src = source
        self._tar = target
        self._features = features

    def _compare_to(self, other):
        return (hash(self), hash(other))

    def features(self):
        return self._features

    def source(self):
        return self._src

    def target(self):
        return self._tar

    def __len__(self):
        return max(self.source(), self.target()) - min(self.source(), self.target())

    def __hash__(self):
        return hash((self._src, self._features['label'], self._tar))

    def __setitem__(self, k, v):
        self._features[k] = v

    def __getitem__(self, k):
        if k in self._features:
            return self._features[k]
        raise AttributeError

    def __str__(self):
        return "%s - %s -> %s" % (self._src, self._features['label'], self._tar)

class Graph(object):
    def __init__(self):
        self._graph_source = defaultdict(dict)
        self._graph_target = defaultdict(OrderedDict)
        self._nodes = {}
        self._edges = set([])
        self._id = None

    def __len__(self):
        return len(self._edges)

    def id(self):
        return self._id

    def order(self):
        return len(self._nodes)

    def set_id(self, _id_):
        self._id = _id_

    def add_node(self, node):
        self._nodes[node.index()] = node

    def add_edge(self, edge):
        self._edges.add(edge)
        self._graph_source[edge.source()][edge.target()] = edge
        self._graph_target[edge.target()][edge.source()] = edge

    def edges(self):
        return self._edges

    def edge(self, source, target):
        if source in self._graph_source and target in self._graph_source[source]:
            return self._graph_source[source][target]
        raise AttributeError

    def hasEdge(self, e):
        if e in self._edges:
            return True
        else:
            return False

    def targets_of(self, source):
        src = source
        if isinstance(source, Node):
           src = source.index()

        if src in self._graph_source:
            return self._graph_source[src]
        raise AttributeError

    def sources_of(self, target):
        tar = target
        if isinstance(target, Node):
            tar = target.index()

        if tar in self._graph_target:
            return self._graph_target[tar]
        raise AttributeError

    def edges_of(self, node):
        edges = []
        if node in self._graph_source:
            edges.extend(self._graph_source[node].values())
        if node in self._graph_target:
            edges.extend(self._graph_target[node].values())
        if len(edges) > 0:
            return edges
        else:
            raise AttributeError

    def node(self, index):
        if index in self._nodes:
            return self._nodes[index]
        raise AttributeError

    def nodes(self):
        return sorted( list(self._nodes.values()) )

    def edges_have_direct_cycle(self, src, tar):
        if src in self._graph_source:
            if tar in self._graph_source[src]:
                if tar in self._graph_source:
                    if src in self._graph_source[tar]:
                        return True
        return False

    def remove_edge(self, edge):
        src, tar = edge.source(), edge.target()
        self._edges.discard(edge)
        if src in self._graph_source:
            if tar in self._graph_source[src]:
                del self._graph_source[src][tar]
                del self._graph_target[tar][src]
        #if tar in self._graph_source:
        #    if src in self._graph_source[tar]:
        #        del self._graph_source[tar][src]
        #        del self._graph_target[src][tar]

    def crossing_edges(self):
        def is_crossing(e1, e2):
            '''
            Crossing followed Gomez-Rodriguez and Nivre article (2013)
            "Divisible Transition Systems and Multiplanar Dependency Parsing"
            '''
            head1, dep1 = e1.source(), e1.target()
            head2, dep2 = e2.source(), e2.target()

            max1, max2 = max(head1, dep1), max(head2, dep2)
            min1, min2 = min(head1, dep1), min(head2, dep2)

            if min1 < min2 < max1 < max2 or min2 < min1 < max2 < max1:
                return True
            else:
                return False

        crossings = set()
        for e1 in self._edges:
            for e2 in self._edges:
                if is_crossing(e1, e2):
                    crossings.add(e1)
                    crossings.add(e2)
        return crossings


    @staticmethod
    def strongly_connected_components(graph):
        """ Find the strongly connected components in a graph using
        Tarjan's algorithm.
        """

        result = [ ]
        stack = [ ]
        low = { }

        def visit(node):
            if node in low: return

            num = len(low)
            low[node] = num
            stack_pos = len(stack)
            stack.append(node)

            try:
                for successor in graph.targets_of(node):
                    visit(successor)
                    low[node] = min(low[node], low[successor])
            except AttributeError:
                pass

            if num == low[node]:
                component = tuple(stack[stack_pos:])
                del stack[stack_pos:]
                if len(component) > 1:
                    result.append(component)
                for item in component:
                    low[item] = graph.order()

        for node in graph.nodes():
            visit(node.index())

        return result

    @staticmethod
    def DFSDecomposition(graph, priority = ("LEFT", "MIN", "LABEL")):
        def ordering(priority, edge):
            def left(edge):
                return (edge.source() - edge.target()) >= 0
            def dist(edge):
                return abs(edge.source() - edge.target())
            def label(edge):
                return edge['label']

            o = []
            for p in priority:
                if p == "LEFT":
                    o.append( int(not left(edge)) )
                elif p == "RIGHT":
                    o.append( int(left(edge)) )
                elif p == "MIN":
                    o.append(dist(edge))
                elif p == "LABEL":
                    o.append(label(edge))
            return tuple(o)

        def rec(G, v, order, visited = set(), visited_edges = set()):
            visited.add(v)
            try:targets = G.targets_of(v)
            except AttributeError: targets = {}

            #try:sources = G.sources_of(v)
            #except AttributeError: sources = {}
            edges = [targets[i] for i in targets] #+ [sources[i] for i in sources]

            partial_ordering = functools.partial(ordering, priority)
            edges = sorted(edges, key=partial_ordering)
            for edge in edges:
                w = edge.source() if edge.source() != v else edge.target()
                if edge not in visited_edges:
                    order.append(edge)
                    visited_edges.add(edge)

                if w not in visited:
                    rec(G, w, order, visited)
                order.append("backtrack")

        order = []
        visited = set()
        for n in graph.nodes():
            if n not in visited:
                rec(graph, graph.nodes()[0], order, visited)
        return order

def print_graph(g, mode = "sagae", out=sys.stdout):
    if mode not in ["sagae", "deepsequoia"]:
        print("Invalid mode. Mode should be 'sagae' or 'deepsequoia'", file=sys.stderr)
        return

    for n in g.nodes()[1:]: #Skip 0 node
        feats = n.features()
        idx   = n.index()

        try:
            sources = g.sources_of(idx).items()
        except AttributeError:
            sources = []

        if len(sources) == 0:
            print("%i\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (idx, feats['token'], feats['lemma'], feats['cpos'], feats['pos'], feats['features'], "", ""), file=out)
        else:
            if mode == "deepsequoia":
                pairs = [(eidx, edge['label']) for eidx, edge in sources]
                pairs = sorted(pairs, key=lambda k:k[0])
                pairs = list(zip(*pairs))
                eidx = "|".join([str(i) for i in pairs[0]])
                labels = "|".join(pairs[1])
                print("%i\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (idx, feats['token'], feats['lemma'], feats['cpos'], feats['pos'], feats['features'], eidx, labels), file=out)
            else:
                for eidx, edge in sources:
                    rel = edge['label']
                    print("%i\t%s\t%s\t%s\t%s\t%s\t%i\t%s" % (idx, feats['token'], feats['lemma'], feats['cpos'], feats['pos'], feats['features'], eidx, rel), file=out)
    print("", file=out)

def read_sagae(fileo):
    kept_id = None
    first   = True
    graph   = Graph()

    with fileo:
        for line in fileo:
            line = line.strip()

            if first:
                first = False
                top_node = Node(0, {'token':'_top_', 'lemma':'_top_', 'cpos':'_', 'pos':'_', 'features':'_'})
                graph.add_node(top_node)


            if line == "":
                #Reset all and produce graph
                kept_id = None
                first = True
                yield graph
                graph = Graph()
                continue

            if line.startswith('#'):
                kept_id = line[1:]
                graph.set_id(kept_id)
                #print >> sys.stderr, "Processing sentence %s" % kept_id
                continue

            items = re.split('  +|\t', line)
            tid, token, lemma, cpos, pos, feats = items[:6]
            node = Node(int(tid), {'token':token, 'lemma':lemma, 'cpos':cpos, 'pos':pos, 'features': feats})

            if int(tid) == 1:
                if node['features'] != '_':
                    f = {k:v for k,v in [s.split('=') for s in node['features'].split('|')]}
                    if 'sentid' in f:
                        #print >> sys.stderr, "Processing sentence %s" % kept_id
                        kept_id = f['sentid']
                        graph.set_id(kept_id)

            if int(tid) == 1 and kept_id is not None:
                if node['features'] == "_":
                    node['features'] = "%s=%s" % ('sentid', kept_id)
                else:
                    f = { k:v for k,v in [i.split('=') for i in node['features'].split('|')] }
                    f['sentid'] = kept_id
                    f = ["%s=%s" % (k,v) for k,v in f.items()]
                    node['features'] = '|'.join(f)

            if len(items) > 8:
                n = 9
                for i in items[8:]:
                    node[ "col_%i" % n ] = i
                    n += 1
            graph.add_node(node)

            if len(items) <= 6 or items[6] == -1:
                continue

            eidx, erel = items[6:8]
            if eidx != "-1" and eidx != "":
                edge = Edge(int(eidx), int(tid), {'label':erel})
                graph.add_edge(edge)

def read_deepsequoia(fileo):
    kept_id = None
    first   = True
    graph   = Graph()

    with fileo:
        for line in fileo:
            line = line.strip()

            if first:
                first = False
                top_node = Node(0, {'token':'_top_', 'lemma':'_top_', 'cpos':'_', 'pos':'_', 'features':'_'})
                graph.add_node(top_node)


            if line == "":
                #Reset all and produce graph
                kept_id = None
                first = True
                yield graph
                graph = Graph()
                continue

            if line.startswith('#'):
                kept_id = line[1:]
                continue

            items = re.split('  +|\t', line)
            tid, token, lemma, cpos, pos, feats = items[:6]
            node = Node(int(tid), {'token':token, 'lemma':lemma, 'cpos':cpos, 'pos':pos, 'features': feats})

            if int(tid) == 1:
                if node['features'] != '_':
                    f = {k:v for k,v in [s.split('=') for s in node['features'].split('|')]}
                    if 'sentid' in f:
                        #print >> sys.stderr, "Processing sentence %s" % kept_id
                        kept_id = f['sentid']

            if int(tid) == 1 and kept_id is not None:
                node['sentid'] = kept_id
            graph.add_node(node)

            if len(items) < 8:
                continue

            edges = items[6:8]
            eindexes, erels = [i for i in edges[0].split('|')], [i for i in edges[1].split('|')]

            if (len(eindexes) == 1 and eindexes[0] == -1) or (len(erels) == 1 and erels[0] == "NONE"):
                continue

            for eidx, erel in zip(eindexes, erels):
                edge = Edge(int(eidx), int(tid), {'label':erel})
                graph.add_edge(edge)
