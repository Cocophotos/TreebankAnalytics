import yaml, argparse, functools

from treebankanalytics.actions import Analyzer, PropertyAnalyzer, VoidAnalyzer, CrossingEdgesAnalyzer, NonPlanarAnalyzer, CyclesAnalyzer, LabelsAnalyzer, EdgeLengthBinsAnalyzer, LexicalLabelPairsAnalyzer, LexicalPairsByLabelAnalyzer, SentenceLengthBinsAnalyzer, DependencyPathsAnalyzer
from treebankanalytics.actions import AllScorer, SentenceBinsScorer, EdgeLengthBinsScorer, LabelsScorer, Scorer, Evaluator, MergeNotDefinedError, FilteredScorer

from treebankanalytics.formatters import *
from treebankanalytics.supported_formats import format_factory_reader, format_factory_writer

import os, re, sys
from treebankanalytics import __version__ as ta_version
__version__ = ta_version

def formatter_factory(f):
    if f == "latex":
        return LaTeXFormatter
    elif f == "csv":
        return CSVFormatter
    else:
        return None

def test_file(t, x):
    """
    'Type' for argparse - checks that file exists and if so open it.
    """
    if not os.path.isfile(x):
        raise argparse.ArgumentError("{0} does not exist".format(x))
    return open(x, t)

def open_yaml_file(stream):
    try:
        return yaml.load(stream.read())
    except yaml.scanner.ScannerError as e:
        print("The config file seems not to be a valid YAML file", file=sys.stderr)
        return None

def should_print_name(config, type):
    if 'General' not in config:
        return True

    key = 'showName{0}'.format(type)
    if key in config['General'] and not config['General'][key]:
        return False
    return True

def options():
    """
    """
    test_file_r = functools.partial(test_file, 'r')
    test_file_w = functools.partial(test_file, 'w')

    parser = argparse.ArgumentParser(prog="TreebankAnalytics %s" % __version__)
    subs = parser.add_subparsers(dest='commands')
    subs.required = True

    converter = subs.add_parser('convert', help="Convert from one format to another", prog="""
Supported formats are:
- sdp (SemEval 2014 task 8 on Broad-coverage semantic dep. parsing)
- sagae (dependency graph format where multi-heads are expressed by repeated tokens)
- sequoia (dependency graph format where multi-heads are separated by a pipe)
- tikz (dependency graph for LaTeX printing (writer only))
- linearize (Using List-based arc eager parsing to linearize the graph and outputting the sequence of actions)
- penman (Using DFS to linearize the graph and outputing a bracketing format closed to the PENMAN notation of AMR)
If you're trying to transform from a CoNLL file to a SDP file,
use sagae or sequoia as CoNLL because they are retro-compatible.

""")
    evaluate  = subs.add_parser('eval', help='Evaluate a system output against a reference')
    analyze   = subs.add_parser('analyze', help='Analyze corpus to extract meaningful information')

    for p in [evaluate, analyze]:
        p.add_argument('-c', '--config', required=True, help='Config file (YAML format)', metavar="FILE", type=test_file_r)
        p.add_argument('-g', '--gold', required=True, help='Gold (reference) file', metavar="FILE", type=test_file_r)
        p.add_argument('-f', '--format', default='sequoia', choices=['sagae', 'sdp', 'sequoia', 'sdp2015'], help='File format to be read')
        p.add_argument('-t', '--table', default='csv', choices=['csv', 'latex'], help='Table formatter')
        p.add_argument('-l', '--lower', default=False, action='store_true', help='Lower edge labels when evaluating or analyzing') 

    evaluate.add_argument('-s', '--system', required=True, help='System file', metavar="FILE", type=test_file_r)
    evaluate.add_argument('-F', '--gold-format', default='sequoia', choices=['sagae', 'sdp', 'sdp2015', 'sequoia'], help='Gold file format to be read')

    converter.add_argument('-f', '--from', required=True, help='Convert from this format', choices=['sdp', 'sdp2015', 'sagae', 'sequoia', 'linearize', 'penman'], dest='ffrom')
    converter.add_argument('-t', '--to', required=True, help='Convert to this format', choices=['sagae', 'sequoia', 'tikz', 'linearize', 'penman'])
    converter.add_argument('path', nargs='?', help='Absolute path to the file', metavar="FILE", type=test_file_r)
    return parser

def main():
    parser = options()
    args   = parser.parse_args()

    if args.commands == "convert":
        reader  = format_factory_reader(args.ffrom)
        writer  = format_factory_writer(args.to)
        with args.path as stream:
            for g in reader(stream):
                writer(g, sys.stdout)
    elif args.commands == "eval":
        config    = open_yaml_file(args.config)
        if config is None:
            sys.exit(-1)

        scorers   = [eval(k) for k in config['Scorers']]
        reader    = format_factory_reader(args.format)
        greader   = format_factory_reader(args.gold_format)
        formatter = formatter_factory(args.table)()
        evaluator = Evaluator(formatter, config, scorers)#[AllScorer, SentenceBinsScorer, EdgeLengthBinsScorer, LabelsScorer])

        print_name = should_print_name(config, 'Scorers')
        for n, t in evaluator.eval(golds=greader(args.gold, args.lower), systems=reader(args.system, args.lower)):
            if print_name:
                print(n)
            print(t)
    elif args.commands == "analyze":
        config    = open_yaml_file(args.config)
        if config is None:
            sys.exit(-1)
        analyzers = [eval(k) for k in config['Analyzers']]
        reader    = format_factory_reader(args.format)
        formatter = formatter_factory(args.table)()
        analyzer  = Analyzer(formatter, config, analyzers)#[VoidAnalyzer, CrossingEdgesAnalyzer, NonPlanarAnalyzer, CyclesAnalyzer, LabelsAnalyzer])

        print_name = should_print_name(config, 'Analyzers')
        for n, t in analyzer.analyze(reader(args.gold)):
            if print_name:
                print(n)
            print(t)

if __name__ == '__main__':
    main()
