import abc, numbers, sys

__all__ = ['compute_f1', 'AllScorer', 'SentenceBinsScorer', 'EdgeLengthBinsScorer', 'LabelsScorer', 'Scorer', 'Evaluator', 'MergeNotDefinedError', 'FilteredScorer']

class MergeNotDefinedError(Exception):
    pass

def compute_f1(recall, precision):
    return 2. * recall * precision / (recall + precision) if (recall + precision) > 0. else 0.

class Scorer(metaclass=abc.ABCMeta):
    def __init__(self, gold, system, config):
        self._g = gold
        self._s = system
        self._config = config
        pass

    @classmethod
    @abc.abstractmethod
    def name(cls):
        pass

    @abc.abstractmethod
    def add_gold(self, edge):
        pass

    @abc.abstractmethod
    def add_system(self, edge):
        pass

    @abc.abstractmethod
    def compute_common(self):
        pass

    @abc.abstractmethod
    def get_results(self):
        pass

    @classmethod
    @abc.abstractmethod
    def table(cls, results, formatter):
        pass


class AllScorer(Scorer):
    def __init__(self, gold, system, config):
        super().__init__(gold, system, config)
        self._gold_lset = set()
        self._gold_uset = set()

        self._system_lset = set()
        self._system_uset = set()

        self._common_lset = set()
        self._common_uset = set()

    @classmethod
    def name(cls):
        return "AllScorer"

    def add_gold(self, e):
        self._gold_lset.add(e)
        self._gold_uset.add((e.source(), e.target()))

    def add_system(self, e):
        self._system_lset.add(e)
        self._system_uset.add((e.source(), e.target()))

    def compute_common(self):
        self._common_lset = self._gold_lset & self._system_lset
        self._common_uset = self._gold_uset & self._system_uset

    def get_results(self):
        return {'LC': len(self._common_lset), 'UC': len(self._common_uset),
                'LG': len(self._gold_lset),   'UG': len(self._gold_uset),
                'LS': len(self._system_lset), 'US': len(self._system_uset)}

    @classmethod
    def table(cls, results, formatter):
        r = {'LP': 0., 'LR': 0., 'LF': 0., 'UP': 0., 'UR': 0., 'UF': 0.}
        r['LP'] =  results['LC'] / results['LS'] if results['LS'] > 0 else 0.
        r['LR'] =  results['LC'] / results['LG'] if results['LG'] > 0 else 0.
        r['UP'] =  results['UC'] / results['US'] if results['US'] > 0 else 0.
        r['UR'] =  results['UC'] / results['UG'] if results['UG'] > 0 else 0.

        r['LF'] = compute_f1(r['LR'], r['LP'])
        r['UF'] = compute_f1(r['UR'], r['UP'])
        table = [ ["LP", "LR", "LF", "UP", "UR", "UF"] ]
        table.append(["%.2f" % (r[k]*100.0,) for k in ('LP', 'LR', 'LF', 'UP', 'UR', 'UF')])
        return formatter.format(table)

class FilteredScorer(AllScorer):
    def __init__(self, gold, system, config):
        super().__init__(gold, system, config)
        self._filtered_labels = set()
        self._keep = False
        self._parse_config()

    @classmethod
    def name(cls):
        return "FilteredScorer"

    def _parse_config(self):
        if not FilteredScorer.name() in self._config:
            return
        scorer = self._config[FilteredScorer.name()]
        if 'filteredLabels' in scorer:
            self._filtered_labels = set(scorer['filteredLabels'])
        if 'keep' in scorer:
            self._keep = scorer['keep']

    def _must_continue_with_this_label(self, label):

        if self._keep: #Do I need to keep the filtered labels
            if label in self._filtered_labels:
                return True
            else:
                return False
        else: #No I don't need to keep filtered_labels:
            if label in self._filtered_labels:
                return False
            else:
                return True

    def add_gold(self, e):
        if not self._must_continue_with_this_label(e['label']):
            return
        self._gold_lset.add(e)
        self._gold_uset.add((e.source(), e.target()))

    def add_system(self, e):
        if not self._must_continue_with_this_label(e['label']):
            return

        self._system_lset.add(e)
        self._system_uset.add((e.source(), e.target()))

class SentenceBinsScorer(AllScorer):
    def __init__(self, gold, system, config):
        super().__init__(gold, system, config)
        self._size = gold.order()
        self._bin_start = 1
        self._bin_end   = 100
        self._bin_step  = 10
        self._parse_config()
        self._bin  = self._determine_bins()

    def _parse_config(self):
        if not SentenceBinsScorer.name() in self._config:
            return
        scorer = self._config[SentenceBinsScorer.name()]
        self._bin_start = scorer['binStart'] if 'binStart' in scorer else 1
        self._bin_end   = scorer['binStop'] if 'binStop' in scorer else 100
        self._bin_step  = scorer['binStep'] if 'binStep' in scorer else 10

    def _determine_bins(self):
        for low,high in zip( range(self._bin_start, self._bin_end+1, self._bin_step),
                             range(self._bin_step, self._bin_end+1, self._bin_step) ):
            if self._size >= low and self._size <= high:
                return "{0}-{1}".format(low, high)
        return "{0}+".format(self._bin_end)

    @classmethod
    def name(cls):
        return "SentenceBinsScorer"

    def get_results(self):
        r = {self._bin: { 'LC': len(self._common_lset), 'UC': len(self._common_uset),
            'LG': len(self._gold_lset), 'UG': len(self._gold_uset),
            'LS': len(self._system_lset), 'US': len(self._system_uset), 'Sent': 1}}
        return r

    @classmethod
    def table(cls, results, formatter):
        def sorting(k):
            info = k[0].split('-')
            if len(info) == 1:
                t = info[0][:-1]
                return (int(t), int(t))
            else:
                return (int(info[0]), int(info[1]))

        for _bin in results:
            r = {'LP': 0., 'LR': 0., 'LF': 0., 'UP': 0., 'UR': 0., 'UF': 0.}
            r['LP'] =  results[_bin]['LC'] / results[_bin]['LS'] if results[_bin]['LS'] > 0 else 0.
            r['LR'] =  results[_bin]['LC'] / results[_bin]['LG'] if results[_bin]['LG'] > 0 else 0.
            r['UP'] =  results[_bin]['UC'] / results[_bin]['US'] if results[_bin]['US'] > 0 else 0.
            r['UR'] =  results[_bin]['UC'] / results[_bin]['UG'] if results[_bin]['UG'] > 0 else 0.

            r['LF'] = compute_f1(r['LR'], r['LP'])
            r['UF'] = compute_f1(r['UR'], r['UP'])
            r['Gold'] = results[_bin]['Sent']
            results[_bin] = r

        table = [ ["Bin", "NumberInGold", "LP", "LR", "LF", "UP", "UR", "UF"] ]


        for _bin, r in sorted(results.items(), key=sorting):
            row = ["%.2f" % (r[k]*100.0,) for k in ('LP', 'LR', 'LF', 'UP', 'UR', 'UF')]
            row.insert(0, str(r['Gold']))
            row.insert(0, _bin)
            table.append(row)
        return formatter.format(table)

class LabelsScorer(AllScorer):
    def __init__(self, gold, system, config):
        super().__init__(gold, system, config)
        self._labels = {}
        self._keep   = True
        self._filtered_labels = set()
        self._parse_config()

    def _parse_config(self):
        if not LabelsScorer.name() in self._config:
            return
        scorer = self._config[LabelsScorer.name()]

        if 'filteredLabels' in scorer:
            self._filtered_labels = set(scorer['filteredLabels'])
        if 'keep' in scorer:
            self._keep = scorer['keep']

    def _must_continue_with_this_label(self, label):
        if self._keep: #Do I need to keep the filtered labels
            if label in self._filtered_labels:
                return True
            else:
                return False
        else: #No I don't need to keep filtered_labels:
            if label in self._filtered_labels:
                return False
            else:
                return True

    def add_gold(self, e):
        label = e['label']
        if not self._must_continue_with_this_label(label):
            return

        if label not in self._labels:
            self._labels[label] = {'LG': set([e]), 'UG': set([(e.source(), e.target())]), 'LS': set(), 'US': set()}
        else:
            self._labels[label]['LG'].add(e)
            self._labels[label]['UG'].add((e.source(), e.target()))

    def add_system(self, e):
        label = e['label']
        if not self._must_continue_with_this_label(label):
            return

        if label not in self._labels:
            self._labels[label] = {'LS': set([e]), 'US': set([(e.source(), e.target())]), 'LG': set(), 'UG': set()}
        else:
            self._labels[label]['LS'].add(e)
            self._labels[label]['US'].add((e.source(), e.target()))

    def compute_common(self):
        for l in self._labels:
            r = self._labels[l]
            r['LC'] = r['LS'] & r['LG']
            r['UC'] = r['US'] & r['UG']

    def get_results(self):
        results = {}
        for l in self._labels:
            r = self._labels[l]
            results[l] = dict([(k, len(v)) for k,v in r.items()])
        return results

    @classmethod
    def name(cls):
        return "LabelsScorer"

    @classmethod
    def table(cls, results, formatter):
        for label in results:
            r = {'Gold': 0., 'LP': 0., 'LR': 0., 'LF': 0., 'UP': 0., 'UR': 0., 'UF': 0.}
            r['LP'] =  results[label]['LC'] / results[label]['LS'] if results[label]['LS'] > 0 else 0.
            r['LR'] =  results[label]['LC'] / results[label]['LG'] if results[label]['LG'] > 0 else 0.
            r['UP'] =  results[label]['UC'] / results[label]['US'] if results[label]['US'] > 0 else 0.
            r['UR'] =  results[label]['UC'] / results[label]['UG'] if results[label]['UG'] > 0 else 0.

            r['LF'] = compute_f1(r['LR'], r['LP'])
            r['UF'] = compute_f1(r['UR'], r['UP'])
            r['Gold'] = results[label]['LG']
            results[label] = r

        table = [ ["Label", 'NumberInGold', "LP", "LR", "LF", "UP", "UR", "UF"] ]
        for label, r in sorted(results.items(), key= lambda k: k[0]):
            row = ["%.2f" % (r[k]*100.0,) for k in ('LP', 'LR', 'LF', 'UP', 'UR', 'UF')]
            row.insert(0, str(r['Gold']))
            row.insert(0, label)
            table.append(row)
        return formatter.format(table)

class EdgeLengthBinsScorer(Scorer):
    def __init__(self, gold, system, config):
        super().__init__(gold, system, config)
        self._bin_start = 1
        self._bin_end   = 100
        self._bin_step  = 10
        self._parse_config()
        self._lengths = {}

    def _parse_config(self):
        if not EdgeLengthBinsScorer.name() in self._config:
            return
        scorer = self._config[EdgeLengthBinsScorer.name()]
        self._bin_start = scorer['binStart'] if 'binStart' in scorer else 1
        self._bin_end   = scorer['binStop'] if 'binStop' in scorer else 100
        self._bin_step  = scorer['binStep'] if 'binStep' in scorer else 10

    def _determine_bins(self, e):
        size = abs( e.source() - e.target() )
        for low,high in zip( range(self._bin_start, self._bin_end+1, self._bin_step), range(self._bin_step, self._bin_end+1, self._bin_step) ):
            if size >= low and size <= high:
                return "{0}-{1}".format(low, high)
        return "{0}+".format(self._bin_end)

    def add_gold(self, e):
        _bin = self._determine_bins(e)
        if _bin not in self._lengths:
            self._lengths[_bin] = {'LG': set([e]), 'UG': set([(e.source(), e.target())]), 'LS': set(), 'US': set()}
        else:
            self._lengths[_bin]['LG'].add(e)
            self._lengths[_bin]['UG'].add((e.source(), e.target()))

    def add_system(self, e):
        _bin = self._determine_bins(e)
        if _bin not in self._lengths:
            self._lengths[_bin] = {'LS': set([e]), 'US': set([(e.source(), e.target())]), 'LG': set(), 'UG': set()}
        else:
            self._lengths[_bin]['LS'].add(e)
            self._lengths[_bin]['US'].add((e.source(), e.target()))

    def compute_common(self):
        for b in self._lengths:
            r = self._lengths[b]
            r['LC'] = r['LS'] & r['LG']
            r['UC'] = r['US'] & r['UG']

    def get_results(self):
        results = {}
        for b in self._lengths:
            r = self._lengths[b]
            results[b] = dict([(k, len(v)) for k,v in r.items()])
        return results

    @classmethod
    def name(cls):
        return "EdgeLengthBinsScorer"

    @classmethod
    def table(cls, results, formatter):
        def sorting(k):
            info = k[0].split('-')
            if len(info) == 1:
                t = info[0][:-1]
                return (int(t), int(t))
            else:
                return (int(info[0]), int(info[1]))

        for _bin in results:
            r = {'Gold': 0., 'LP': 0., 'LR': 0., 'LF': 0., 'UP': 0., 'UR': 0., 'UF': 0.}
            r['LP'] =  results[_bin]['LC'] / results[_bin]['LS'] if results[_bin]['LS'] > 0 else 0.
            r['LR'] =  results[_bin]['LC'] / results[_bin]['LG'] if results[_bin]['LG'] > 0 else 0.
            r['UP'] =  results[_bin]['UC'] / results[_bin]['US'] if results[_bin]['US'] > 0 else 0.
            r['UR'] =  results[_bin]['UC'] / results[_bin]['UG'] if results[_bin]['UG'] > 0 else 0.

            r['LF'] = compute_f1(r['LR'], r['LP'])
            r['UF'] = compute_f1(r['UR'], r['UP'])
            r['Gold'] = results[_bin]['LG']
            #r['System'] = results[_bin]['LS']
            #r['Common'] = results[_bin]['LC']
            results[_bin] = r

        table = [ ["Bin", 'NumberInGold', "LP", "LR", "LF", "UP", "UR", "UF"] ]

        for _bin, r in sorted(results.items(), key=sorting):
            row = ["%.2f" % (r[k]*100.0,) for k in ('LP', 'LR', 'LF', 'UP', 'UR', 'UF')]
            #row.insert(0, str(r['Common']))
            #row.insert(0, str(r['System']))
            row.insert(0, str(r['Gold']))
            row.insert(0, _bin)
            table.append(row)
        return formatter.format(table)

class Evaluator(object):
    def __init__(self, formatter, config, scorers = []):
        self._scorers   = scorers
        self._results   = {}
        self._formatter = formatter
        self._config    = config

    def eval(self, golds, systems):
        for gold, system in zip(golds, systems):
            for scorer in self._scorers:
                sc = scorer(gold, system, self._config)
                for e in gold.edges():
                    sc.add_gold(e)
                for e in system.edges():
                    sc.add_system(e)
                sc.compute_common()
                self._accumulate(sc, scorer.name())

        for scorer in self._scorers:
            yield scorer.name(), scorer.table(self._results[scorer.name()], self._formatter)

    def _accumulate(self, sc, name):
        if name not in self._results:
            self._results[name] = sc.get_results()
        else:
            acc = self._results[name]
            self._merge_dict(acc, sc.get_results())
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


