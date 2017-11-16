import os, re, sys, abc, numbers
from collections import defaultdict
from treebankanalytics.graphs.Graph import Graph, Node

__all__ = ['MergeNotDefinedError', 'Analyzer', 'PropertyAnalyzer', 'VoidAnalyzer',
'CrossingEdgesAnalyzer', 'NonPlanarAnalyzer', 'CyclesAnalyzer', 'LabelsAnalyzer', 'EdgeLengthBinsAnalyzer', 'LexicalLabelPairsAnalyzer', 'LexicalPairsByLabelAnalyzer',
'SentenceLengthBinsAnalyzer', 'DependencyPathsAnalyzer']

class MergeNotDefinedError(Exception):
    pass

class PropertyAnalyzer(object):
    def __init__(self, graph, config):
        self._graph = graph
        self._config = config

    @classmethod
    @abc.abstractmethod
    def name(cls):
        pass

    @abc.abstractmethod
    def analyze(self):
        pass

    @abc.abstractmethod
    def get_results(self):
        pass

    @classmethod
    @abc.abstractmethod
    def table(cls, results, formatter):
        pass

class DependencyPathsAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._length = 2
        self._paths = {}
        self._parse_config()

    def _parse_config(self):
        cls = eval(self.__class__.__name__)
        if not cls.name() in self._config:
            return
        scorer = self._config[cls.name()]
        self._length = scorer['length'] if 'length' in scorer else 2

    @classmethod
    def name(cls):
        return "DependencyPathsAnalyzer"

    def _path_rec(self, parent, labels, paths):
        try:
            targets = self._graph.targets_of(parent)
        except AttributeError:
            targets = {}

        for idx in targets:
            e = targets[idx]
            label = e['label']
            labels.append(label)
            if len(labels) == self._length:
                paths.append("-".join(labels))
                labels.pop(-1)
            else:
                self._path_rec(e.target(), labels, paths)

        if len(labels) > 0:
           labels.pop(-1)

    def analyze(self):
        paths = []
        for nidx in self._graph.nodes()[1:]:
            self._path_rec(nidx, [], paths)
        for path in paths:
            self._paths[path] = self._paths.setdefault(path, 0) + 1

    def get_results(self):
        return {'Paths': self._paths, 'Total': sum(self._paths.values())}

    @classmethod
    def table(cls, results, formatter):
        r = {'Paths': {}}
        total = results['Total']

        for path in results['Paths']:
            r['Paths'][path] = results['Paths'][path] / total * 100.0
        r = sorted(r['Paths'].items(), key= lambda k: k[1], reverse = True)

        table = [['Path', '#', '%', "% Cumulated"]]
        cumul = 0.0
        for path, percent in r:
            table.append([path, str(results['Paths'][path]), str(percent), str(cumul + percent)])
            cumul += percent
        return formatter.format(table)

class LexicalPairsByLabelAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._lex_info = "token"
        self._pairs = defaultdict(dict)
        self._parse_config()

    def _parse_config(self):
        if not LexicalPairsByLabelAnalyzer.name() in self._config:
            return
        scorer = self._config[LexicalPairsByLabelAnalyzer.name()]
        self._lex_info = scorer['lexical'] if 'lexical' in scorer else "token"

        if self._lex_info not in ('token', 'lemma', 'pos', 'cpos'):
            raise KeyError('lexical option for %s should be token or lemma or cpos or pos' % LexicalPairsByLabelAnalyzer.name())

    @classmethod
    def name(cls):
        return "LexicalPairsByLabelAnalyzer"

    def _get_lex_info(self, nidx):
        node = self._graph.node(nidx)
        return node[self._lex_info]

    def analyze(self):
        for e in self._graph.edges():
            label = e['label']
            p     = (self._get_lex_info(e.source()), self._get_lex_info(e.target()))
            self._pairs[label][p] = self._pairs[label].setdefault(p, 0) + 1

    def get_results(self):
        return {'Edges': len(self._graph), 'Pairs': self._pairs, 'Nodes': self._graph.order()}

    @classmethod
    def table(cls, results, formatter):
        r = {'Pairs': defaultdict(dict)}
        for label in results['Pairs']:
            for s, t in results['Pairs'][label]:
                r['Pairs'][label]["%s / %s" % (s, t)] = results['Pairs'][label][(s,t)]

        sorted_ = {}
        for label in r['Pairs']:
            ssorted_ = sorted( r['Pairs'][label].items(), key=lambda k: k[1], reverse=True )
            sorted_[label] = ssorted_
        sorted_ = sorted( sorted_.items(), key=lambda k: k[0] )

        table = [['Label', 'Pair', '#']]
        for label, list_of_pairs in sorted_:
            for pair, freq in list_of_pairs:
                table.append([label, pair, str(freq)])
        return formatter.format(table)


class LexicalLabelPairsAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._lex_info = "token"
        self._type = "head"
        self._pairs = {}
        self._parse_config()

    def _parse_config(self):
        if not LexicalLabelPairsAnalyzer.name() in self._config:
            return
        scorer = self._config[LexicalLabelPairsAnalyzer.name()]
        self._lex_info = scorer['lexical'] if 'lexical' in scorer else "token"
        self._type     = scorer['type'] if 'type' in scorer else 'head'

        if self._lex_info not in ('token', 'lemma', 'pos', 'cpos'):
            raise KeyError('lexical option for %s should be token or lemma or cpos or pos' % LexicalLabelPairsAnalyzer.name())
        if self._type not in ('head', 'dependent', 'both'):
            raise KeyError('lexical option for %s should be head or dependent or both' % LexicalLabelPairsAnalyzer.name())

    @classmethod
    def name(cls):
        return "LexicalLabelPairsAnalyzer"

    def _get_lex_info(self, nidx):
        node = self._graph.node(nidx)
        return node[self._lex_info]

    def _get_lex(self, edge):
        if self._type == "head":
            yield edge.source()
        elif self._type == "dependent":
            yield edge.target()
        else:
            yield edge.source()
            yield edge.target()

    def analyze(self):
        for e in self._graph.edges():
            label = e['label']
            for nidx in self._get_lex(e):
                lex   = self._get_lex_info(nidx)
                self._pairs[(lex, label)] = self._pairs.setdefault((lex, label), 0) + 1

    def get_results(self):
        return {'Edges': len(self._graph), 'Pairs': self._pairs, 'Nodes': self._graph.order()}

    @classmethod
    def table(cls, results, formatter):
        r = {'Pairs': {}}
        for lex, label in results['Pairs']:
            p = (lex, label)
            r['Pairs']["%s / %s" % (lex, label)] = results['Pairs'][p]

        sorted_ = sorted(r['Pairs'].items(), key=lambda k: k[1], reverse=True)

        table = [['Pair', '#']]
        for label, percent in sorted_:
            table.append([label, str(r['Pairs'][label])])
        return formatter.format(table)


class LabelsAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._labels = {}

    @classmethod
    def name(cls):
        return "LabelsAnalyzer"

    def analyze(self):
        for e in self._graph.edges():
            label = e['label']
            self._labels[label] = self._labels.setdefault(label, 0) + 1

    def get_results(self):
        return {'Edges': len(self._graph), 'Labels': self._labels}

    @classmethod
    def table(cls, results, formatter):
        r = {'Percents': {}, 'Labels': {}}
        for label in results['Labels']:
            r['Percents'][label] = results['Labels'][label] / results['Edges'] * 100.0
            r['Labels'][label]   = results['Labels'][label]

        sorted_percents = sorted(r['Percents'].items(), key=lambda k: k[1], reverse=True)

        table = [['Label', '#', '%', '% Cumulated']]
        cumul = 0.0
        for label, percent in sorted_percents:
            table.append([label, str(r['Labels'][label]), str(percent), str(cumul + percent)])
            cumul += percent
        return formatter.format(table)

class EdgeLengthBinsAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._lengths = {}
        self._bin_start = 1
        self._bin_end   = 100
        self._bin_step  = 10
        self._parse_config()

    @classmethod
    def name(cls):
        return "EdgeLengthBinsAnalyzer"

    def _parse_config(self):
        if not EdgeLengthBinsAnalyzer.name() in self._config:
            return
        scorer = self._config[EdgeLengthBinsAnalyzer.name()]
        self._bin_start = scorer['binStart'] if 'binStart' in scorer else 1
        self._bin_end   = scorer['binStop'] if 'binStop' in scorer else 100
        self._bin_step  = scorer['binStep'] if 'binStep' in scorer else 10

    def _determine_bins(self, e):
        size = abs( e.source() - e.target() )
        for low,high in zip( range(self._bin_start, self._bin_end+1, self._bin_step), range(self._bin_step, self._bin_end+1, self._bin_step) ):
            if size >= low and size <= high:
                return "{0}-{1}".format(low, high)
        return "{0}+".format(self._bin_end)

    def analyze(self):
        for e in self._graph.edges():
            _bin = self._determine_bins(e)
            self._lengths[_bin] = self._lengths.setdefault(_bin, 0) + 1

    def get_results(self):
        return {'Edges': len(self._graph), 'Lengths': self._lengths}

    @classmethod
    def table(cls, results, formatter):
        def sorting(k):
            info = k[0].split('-')
            if len(info) == 1:
                t = info[0][:-1]
                return (int(t), int(t))
            else:
                return (int(info[0]), int(info[1]))

        r = {'Percents': {}, 'Lengths': {}}
        for dist in results['Lengths']:
            r['Percents'][dist] = results['Lengths'][dist] / results['Edges'] * 100.0
            r['Lengths'][dist]   = results['Lengths'][dist]

        sorted_percents = sorted(r['Percents'].items(), key=sorting)

        table = [['Length', '#', '%']]
        cumul = 0.0
        for dist, percent in sorted_percents:
            table.append([dist, str(r['Lengths'][dist]), str(percent)])
            cumul += percent
        return formatter.format(table)

class SentenceLengthBinsAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._lengths = {}
        self._bin_start = 1
        self._bin_end   = 100
        self._bin_step  = 10
        self._parse_config()

    @classmethod
    def name(cls):
        return "SentenceLengthBinsAnalyzer"

    def _parse_config(self):
        if not SentenceLengthBinsAnalyzer.name() in self._config:
            return
        scorer = self._config[SentenceLengthBinsAnalyzer.name()]
        self._bin_start = scorer['binStart'] if 'binStart' in scorer else 1
        self._bin_end   = scorer['binStop'] if 'binStop' in scorer else 100
        self._bin_step  = scorer['binStep'] if 'binStep' in scorer else 10

    def _determine_bins(self, e):
        for low,high in zip( range(self._bin_start, self._bin_end+1, self._bin_step), range(self._bin_step, self._bin_end+1, self._bin_step) ):
            if e >= low and e <= high:
                return "{0}-{1}".format(low, high)
        return "{0}+".format(self._bin_end)

    def analyze(self):
        _bin = self._determine_bins(self._graph.order())
        self._lengths[_bin] = self._lengths.setdefault(_bin, 0) + 1

    def get_results(self):
        return {'Lengths': self._lengths, 'Total': 1}

    @classmethod
    def table(cls, results, formatter):
        def sorting(k):
            info = k[0].split('-')
            if len(info) == 1:
                t = info[0][:-1]
                return (int(t), int(t))
            else:
                return (int(info[0]), int(info[1]))

        r = {'Percents': {}, 'Lengths': {}}
        for dist in results['Lengths']:
            r['Percents'][dist] = results['Lengths'][dist] / results['Total'] * 100.0
            r['Lengths'][dist]   = results['Lengths'][dist]

        sorted_percents = sorted(r['Percents'].items(), key=sorting)

        table = [['Length', '#', '%']]
        cumul = 0.0
        for dist, percent in sorted_percents:
            table.append([dist, str(r['Lengths'][dist]), str(percent)])
            cumul += percent
        return formatter.format(table)

class CyclesAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._cycles = 0

    @classmethod
    def name(cls):
        return "CyclesAnalyzer"

    def analyze(self):
        self._cycles = len(Graph.strongly_connected_components(self._graph))

    def get_results(self):
        return {'Graphs': 1, 'DAGs': 0 if self._cycles > 0 else 1, 'Cycles': self._cycles}

    @classmethod
    def table(cls, results, formatter):
        r = [results['Graphs'], results['DAGs'], results['DAGs'] / results['Graphs'] * 100.0, results['Cycles']]
        table = [['# Graphs', '# DAGs', '% DAGs', '# Cycles']]
        table.append([str(e) for e in r])
        return formatter.format(table)


class NonPlanarAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._non_planar = 0

    @classmethod
    def name(cls):
        return "NonPlanarAnalyzer"

    def analyze(self):
        self._non_planar = 1 if len(self._graph.crossing_edges()) > 0 else 0

    def get_results(self):
        return {'Graphs': 1, 'NonPlanar': self._non_planar}

    @classmethod
    def table(cls, results, formatter):
        r = [results['Graphs'], results['NonPlanar'], results['NonPlanar'] / results['Graphs'] * 100.0]
        table = [['# Graphs', '# Non Planar Graphs', '% Non Planar Graphs']]
        table.append([str(e) for e in r])
        return formatter.format(table)

class CrossingEdgesAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._size = len(self._graph)
        self._crossings  = 0

    @classmethod
    def name(cls):
        return "CrossingEdgesAnalyzer"

    def analyze(self):
        self._crossings += len(self._graph.crossing_edges()) / 2

    def get_results(self):
        return {'Edges': self._size, 'Crossings': self._crossings}

    @classmethod
    def table(cls, results, formatter):
        r = [results['Edges'], results['Crossings'], results['Crossings'] / results['Edges'] * 100.0]
        table = [['# Edges', '# Crossings Edges', '% Crossings Edges']]
        table.append([str(e) for e in r])
        return formatter.format(table)

class VoidAnalyzer(PropertyAnalyzer):
    def __init__(self, graph, config):
        super().__init__(graph, config)
        self._order = self._graph.order()
        self._labels_as_void = set()
        self._void  = 0
        self._parse_config()

    def _parse_config(self):
        if not VoidAnalyzer.name() in self._config:
            return
        scorer = self._config[VoidAnalyzer.name()]
        if not 'void_labels' in scorer:
            return
        self._labels_as_void = set(scorer['void_labels'])

    @classmethod
    def name(cls):
        return "VoidAnalyzer"

    def analyze(self):
        for n in self._graph.nodes():
            try:
                edges = self._graph.edges_of(n)
                for edge in edges:
                    if edge['label'] in self._labels_as_void:
                        self._void += 1
            except AttributeError:
                self._void += 1

    def get_results(self):
        return {'Tokens': self._order, 'Void': self._void}

    @classmethod
    def table(cls, results, formatter):
        r = [results['Tokens'], results['Void'], results['Void'] / results['Tokens'] * 100.0]
        table = [['# Tokens', '# Void', '% Void']]
        table.append([str(e) for e in r])
        return formatter.format(table)


class Analyzer(object):
    def __init__(self, formatter, config, analyzers = []):
        self._analyzers = analyzers
        self._formatter = formatter
        self._results   = {}
        self._config    = config

    def analyze(self, graphs):
        for graph in graphs:
            for analyzer in self._analyzers:
                an = analyzer(graph, self._config)
                an.analyze()
                self._accumulate(an, analyzer.name())
        for analyzer in self._analyzers:
            yield analyzer.name(), analyzer.table(self._results[analyzer.name()], self._formatter)

    def _accumulate(self, an, name):
        if name not in self._results:
            self._results[name] = an.get_results()
        else:
            acc = self._results[name]
            self._merge_dict(acc, an.get_results())
            self._results[name] = acc

    def _merge_dict(self, result, add):
        for i, k in enumerate(add):
            if not isinstance(add, list) and k not in result:
                result[k] = add[k]
            else:
                if isinstance(add, list):
                    v = k
                else:
                    v = add[k]

                if isinstance(v, numbers.Number):
                    if isinstance(add, list):
                        results[i] += v
                    else:
                        result[k] += v
                elif isinstance(v, list) or isinstance(v, dict):
                    self._merge_dict(result[k], v)
                else:
                    raise MergeNotDefinedError('Merge not defined for this type (%s, %s)' % (str(v), type(v)) )
