# TreebankAnalytics

# What is it?

TreebankAnalytics is a NLP tool that helps you compute valuable information on graphbanks: deep syntactic corpora such as those released for the [SemEval 2014 task 8 shared task](http://alt.qcri.org/semeval2014/task8/) (Broad-coverage semantic dependency parsing) or such as the [DeepSequoia](http://deep-sequoia.inria.fr/), a graph-based deep syntax treebank for French. 

- Analyzing the treebank to extract interesting properties (% of cycles, non planar graphs, number of nodes that are semantically void, ...).
- Evaluating a system output against gold reference and extract different kind of stats:
    * Classic precision/recall/f-score metrics
    * Breakdown by labels (possibility to exclude ou keep certain labels)
    * Breakdown by sentence bins (possibility to set bin size, etc)
    * Classic precision/recall/f-score metrics with some labels left out
    * Classics precision/recall/f-score metrics on certain labels only
    * ... 
- Converting input format into a different output format.

# How to install

TreebankAnalytics is developped with Python 3, so you need a recent version of Python 3 such as Python 3.2 and above. You can install it by cloning this repository and run (*sudo* may be necessary to execute this command):

```bash
python3 setup.py install
```

The setup.py script will take care of dependencies for you (PyYAML only for now).

# Formats

TreebankAnalytics supports the following formats: 

- deepsequoia format (called `sequoia` in the software) which is used to annotate the [DeepSequoia](http://deep-sequoia.inria.fr/).
- `sdp` format: the one used during [SemEval 2014 shared task](http://alt.qcri.org/semeval2014/task8/).
- `sagae` format: the one used in the DAGParser adapted from [Sagae and Tsujii (2008)](http://people.ict.usc.edu/~sagae/docs/sagae-coling08.pdf). The format is an extension of the CoNLL format that encodes multi-governors by repeating the token with a different head id and label.
- Standard CoNLL-X format (since `sequoia` and `sagae` are both retro-compatible).

## My format is not supported.

You can add your own format through a simple API.
TBA

# Analyzers

TreebankAnalytics is shipped with several kinds of analyzers:

- `VoidAnalyzer` which analyzes the number of semantically empty tokens (ie. no incoming or outgoing edges) in a treebank.
- `CrossingEdgesAnalyzer` which analyzes the number of crossing edges in a treebank.
- `NonPlanarAnalyzer` which analyzes the number of non planar graphs in a treebank.
- `CyclesAnalyze` which analyzes the number of cycles, graphs and DAGs in a treebank.
- `LabelsAnalyzer` which analyzes the labels distribution in a treebank.

## Using analyzers

Analyzers are used through the `analyze` command (`TreebankAnalytics analyze -h` for more details). Analyzers are customizable by using a configuration file in a [YAML](http://yaml.org/) format.

In this config file, you need to specify which analyzers you'd like to use:

```yaml
Analyzers :
    - VoidAnalyzer
    - NonPlanarAnalyzer
```

This will use two different analyzers (`VoidAnalyzer`, `NonPlanarAnalyzer`). 

# Scorers

TreebankAnalytics is shipped with several kinds of scorers:

- `AllScorer` which gives the Labeled precision (LP), recall (LR) and F-score (LF) as well as the Unlabeled precision (UP), recall (UR) and f-score (UF).
- `LabelsScorer` which gives the LP/LR/LF and UP/UR/UF for each label type.
- `FilteredScorer` which gives the global LP/LR/LF and UP/UR/UF for certain labels only (or for all labels except those you specify).
- `SentenceBinsScorer` which gives the LP/LR/LF and UP/UR/UF grouped by sentence bins.
- `EdgeLengthBinsScorer` which is the same as SentenceBinsScorer but for edge length (undirected distance between head and dependent).

## Using scorers

Scorers are used through the `eval` command (`TreebankAnalytics eval -h` for more details). Scorers are customizable by using a configuration file in a [YAML](http://yaml.org/) format.

In this config file, you need to specify which scorers you'd like to use:

```yaml
Scorers :
    - AllScorer
    - LabelsScorer
    - FilteredScorer
```

This will use three different scorers (`AllScorer`, `LabelsScorer`, `FilteredScorer`). You can also customize every single scorer. See the description of scorers' options below.


### AllScorer

No customization available.

### SentenceBinsScorer & EdgeLengthBinsScorer

Available options:

- `binStart` (type: *integer*): give the starting point of the first bin (default = 1).
- `binStop` (type: *integer*): give the end point of the last bin. All sentences above this threshold will be agregated in a single group (default = 100).
- `binStep` (type: *integer*): size of the bin (default = 10)

The default options gives bins like this :
```
1-10
11-20
21-30
...
41-50
...
90-100
100+
```
### LabelsScorer

Available options:

- filteredLabels (type: *list*): list of labels (default = []).
- keep (type: *boolean*): should we keep the filteredLabels (default = true)

If keep is true, the scorer only shows the filteredLabels, if keep is false, the scorer shows all labels except the filtered ones.

Example:
```
LabelsScorer:
    filteredLabels:
        - nsubj
        - nmod
    keep: true
```

This gives:

| Label | NumberInGold | LP  | LR  | LF  | UP  | UR  | UF   |
| ----- | ------------ | --- | --- | --- | --- | --- | ---- |
| nsubj | 8000         | 90  | 90  | 90  | 92  | 93  | 91.5 |
| nmod  | 6000         | ..  | ..  | ..  | ..  | ..  | ..   |

### FilteredScorer

Available options:

- filteredLabels (type: *list*): list of labels (default = []).
- keep (type: *boolean*): should we keep the filteredLabels (default = false)

If `keep` is *true*, the scorer only compute the LP/LR/LF and UP/UR/UF for these labels. If `keep` is *false*, the scorer compute the scores for all labels except the filtered ones.

### Default config

You always need to give a config file (there is no default). A standard config file would be the following one:

```yaml
Scorers:
    - AllScorer
```

# General options

Some options may be specified for both `Analyzers` and `Scorers`:

```yaml
General: 
    showNameScorers: true | false
    showNameAnalyzers: true | false
```

The first option (`showNameScorers`) will output the name of each scorer before giving the result or not.
The second option (`showNameAnalyzers`) will output the name of each analyzer before giving the result or not.

Example (`showNameScorers` is set to *true*):

```
AllScorer
LP    LR    LF    UP     UR    UF
90    85    87    90     85    87
```

Example (`showNameScorers` is set to *false*):
```
LP    LR    LF    UP     UR    UF
90    85    87    90     85    87
```

This option is useful when you want to output usable CSV file for pgfplots for example.

# Converters

## Using converters

You can convert from one format to another, by specifying the input format and the output format. See `TreebankAnalytics convert -h` for more details.

# How to cite

If you're using the software, please cite the following work :

Corentin Ribeyre, Méthodes d’Analyse Supervisée pour l’Interface Syntaxe-Sémantique, PhD Thesis, Université Paris 7 Diderot, 2015 (to appear).

```bib
@phdthesis{ribeyre:2015:phd,
title = {{Méthodes d'Analyse Supervisée pour l'Interface Syntaxe-Sémantique}},
author = {Ribeyre, Corentin},
school = {Universit{\'{e}} Paris 7 Diderot},
year = {2015},
note = {to appear}
}
```
