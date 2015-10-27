import io

__all__ = ['LaTeXFormatter']

class LaTeXFormatter(object):
    def __init__(self):
        pass

    def format(self, table):
        output = io.StringIO()
        print("\\begin{tabular}{{{0}}}".format("c"*len(table[0])), file=output)
        print("\t\\toprule", file=output)
        print("\t{0}\\\\".format(" & ".join(table[0])), file=output)
        print("\t\\midrule", file=output)
        for row in table[1:]:
            print("\t{0}\\\\".format(' & '.join(row)), file=output)
        print("\t\\bottomrule", file=output)
        print("\\end{tabular}")

        c = output.getvalue()
        output.close()
        return c
