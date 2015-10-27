import io

__all__ = ['CSVFormatter']

class CSVFormatter(object):
    def __init__(self):
        pass

    def format(self, table):
        output = io.StringIO()
        for row in table:
            print('\t'.join(row), file=output)
        c = output.getvalue()
        output.close()
        return c
