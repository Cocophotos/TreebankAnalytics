import os, re, sys

import treebankanalytics.readers as readers
import treebankanalytics.writers as writers
__all__ = ['format_factory_reader', 'format_factory_writer']

def _format_factory(f, type):
    try:
        reader = eval('%ss.%s.%s_%s' % (type, f, f, type))
        return reader
    except:
        print("Format %s is not supported as a %s" % (f, type), file=sys.stderr)
        return None

def format_factory_reader(f):
    return _format_factory(f, 'reader')

def format_factory_writer(f):
    return _format_factory(f, 'writer')
