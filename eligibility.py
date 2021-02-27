import json
import csv
import itertools
from pprint import pprint
from collections import namedtuple

import numpy as np
from sympy.core import Symbol
from sympy.logic import SOPform
from sympy.logic.boolalg import And, Not

SympyConfig = namedtuple('SympyConfig', 'vmap symbols')

class TruthTable():
    def __init__(self, qmap, rows):
        self.sympy_configs = {}
        self.rows = []
        self.symbols = []
        self.columns = self._get_column_order(rows)
        self._init_sympy_config(qmap)
        self._format_rows(rows)

    def simplify(self):
        res = SOPform(self.symbols, self.rows)
        # iterate through the individual And terms
        for and_term in res.args:
            required_conditions = []
            for var in and_term.args:
                # Only care about what's required
                if not isinstance(var, Not):
                    required_conditions.append(var)
        #
            print(required_conditions)
            # print(type(thing))
        # print(type(res))
        # print(dir(res))
        # for a in res.args[0].args:
        #     print(a)
        # print(len(res.args))

    def _init_sympy_config(self, qmap):
        for id in self.columns:
            num_opts = len(qmap[id])
            vmap = {}
            for i, opt in enumerate(qmap[id]):
                symbols = []
                # Generate symbol
                self.symbols.append(Symbol(opt))

                # Generate binary minterm array
                a = np.array([1])
                a = np.pad(a, (i, num_opts - i - 1), 'constant')
                vmap[opt] = a.tolist()

            self.sympy_configs[id] = SympyConfig(vmap, symbols)

    def _get_column_order(self, rows):
        # We don't care about eligiblity. Should already be filtered
        r = rows[0]
        del r['eligible']
        return sorted(r.keys())

        # return ['q.screening.eligibility.age.range']

    def _format_rows(self, rows):
        for row in rows:
            formatted = []
            for column in self.columns:
                value = row[column]
                formatted.extend(self.sympy_configs[column].vmap[value])
            
            self.rows.append(formatted)


def get_question_map(config):
    qmap = {}
    for question in config['eligibilityQuestions']:
        if question['required'] and 'options' in question:
            id = question['id']
            options = [option['value'] for option in question['options']]
            qmap[id] = sorted(options)

    return qmap

def main():
    with open('config.json') as cf, open('data/02-21-2021.csv') as df:
        config = json.loads(cf.read())
        qmap = get_question_map(config)
        rows = [r for r in csv.DictReader(df, delimiter='\t')
            if r['eligible'] == 'true'
            # if r['eligible'] == 'true' and
            #     r['q.screening.eligibility.county'] == 'Alameda'
        ]
    # pprint(rows)
    # print(len(rows))

    # tt = TruthTable(qmap, rows[:5])
    tt = TruthTable(qmap, rows)
    tt.simplify()
    # print(tt.columns)
    # print(tt.symbols)
    # pprint(rows[:5])
    # for r in tt.rows[:1]:
    #     for col, sym in zip(r, tt.symbols):
    #         print(sym, col)
    #
    # print(tt.columns)
    # print(len(tt.symbols))
    # print(len(tt.rows[1]))
    # print(len(tt.rows[2]))
    # pprint(tt.sympy_configs[''])

    # tt.simplify()


if __name__ == '__main__':
    main()
