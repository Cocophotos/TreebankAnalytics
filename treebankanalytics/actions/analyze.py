import os, re, sys, abc, numbers
from treebankanalytics.graphs.Graph import Graph

__all__ = ['MergeNotDefinedError', 'Analyzer', 'PropertyAnalyzer', 'VoidAnalyzer',
'CrossingEdgesAnalyzer', 'NonPlanarAnalyzer', 'CyclesAnalyzer', 'LabelsAnalyzer']

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
