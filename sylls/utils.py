import math
from json import load
import random
import re
from pathlib import Path
from typing import Iterator, List

import numpy as np

default_th = .001
default_th_trans = .0005


def get_onset_nucleus_coda(syll: str) -> [str, str, str]:
    m = re.match(r'^([^aeiou]*)([aeiou ]+)([^aeiou]*)$', syll)
    if not m:
        print(syll)
    return map(lambda x: str(x).strip(), m.groups())


def get_logprob(graph: dict, phones: str, totals: dict) -> float:
    sylls = phones.split('.')
    out = 0
    prev = None
    for syll in sylls:
        o, n, c = get_onset_nucleus_coda(syll.replace('ˈ', ''))
        if prev:
            out += math.log2(totals['transitions'] / graph['transitions'].get(prev + '|' + o.split(' ')[0], 1))
        for k, key in [(o, 'onset'), (n, 'nucleus'), (c, 'coda')]:
            out += math.log2(totals[key]) - math.log2(graph[key].get(k, 1))
        prev = c
    out += math.log2(totals['transitions'] / graph['transitions'].get(prev + '|$', 1))
    if len(sylls) > 1:
        for j, syll in enumerate(reversed(sylls)):
            if 'ˈ' in syll:
                out += math.log2(totals['tonic'] / graph['tonic'].get(str(j), 1))
                break
        else:
            out += math.log2(totals['tonic'])
    out += math.log2(totals['n_sylls'] / graph['n_sylls'].get(str(len(sylls)), 1))
    return out


def get_total_words(graph, n_sylls: int, totals: dict, th: float = default_th, th_trans: float = default_th_trans, verbose: bool = False) -> int:
    ons = sum(1 for k in graph['onset'] if graph['onset'][k] / totals['onset'] >= th and k != 'ɾ')
    nuc = 31
    trans = len({f'{cod}|{ons}' for cod in graph['coda'] for ons in graph['onset']
                 if graph['coda'][cod] >= th / totals['coda'] and graph['onset'][ons] / totals['onset'] >= th
                 and graph['transitions'].get(f'{cod}|{ons.split(" ")[0]}', -1) / totals['transitions'] >= th_trans})
    end = sum(1 for k in graph['coda']
              if graph['coda'][k] >= th / totals['coda']
              and graph['transitions'].get(f'{k}|$', -1) / totals['transitions'] >= th_trans)
    if verbose:
        print(f'I = {ons}', f'N = {nuc}', f'T = {trans}', f'F = {end}', f'n = {n_sylls}', sep='\t')
    return ons * nuc ** n_sylls * trans ** (n_sylls - 1) * end * min(n_sylls, 3)


def accent(syll: str) -> str:
    if any(c in syll for c in 'aeo'):
        return syll.replace('a', 'á').replace('e', 'é').replace('o', 'ó')
    elif any(c in syll for c in ['ui', 'iu']):
        return syll.replace('ui', 'uí').replace('iu', 'iú')
    return syll.replace('i', 'í').replace('u', 'ú')


ph_dicts = [
    {
        re.compile(r'k([ei])'): r'qu\1',
        re.compile(r'θ([ei])'): r'c\1',
        re.compile(r'g[uw]([ei])'): r'gü\1',
        re.compile(r'^i([aeou])'): r'hi\1',
        re.compile(r'^u([aeoi])'): r'hu\1',
        '[aeiou].r': 'rr',
        'tʃ': 'ch',
        'ɲ': 'ñ',
        'ʎ': 'll',
        'ʝ': 'y',
        'x': 'j',
    }, {
        re.compile(r'[ck](\.?)s'): r'\1x',
        'k': 'c',
        '\u027e': 'r',
        'θ': 'z',
        re.compile(r'g([ei])'): r'gu\1',
    }
]


def phones_to_graphemes(phones: str) -> str:
    out = phones.replace(' ', '')
    for d in ph_dicts:
        for k in d:
            if isinstance(k, re.Pattern):
                out = re.sub(k, d[k], out)
            elif isinstance(k, str):
                out = out.replace(k, d[k])
    sylls = out.split('.')
    if len(sylls) == 1:
        return out.replace('ˈ', '')
    for j, syll in enumerate(reversed(sylls)):
        if 'ˈ' in syll:
            if ((j == 0 and any(syll.endswith(c) for c in 'aeiouns'))
                or (j == 1 and not any(sylls[-1].endswith(c) for c in 'aeiouns'))
                or j > 1
                or (''.join(c for c in syll if c in 'aeiou') in ['i', 'u'] and
                    ((j > 0 and any(syll.endswith(c) for c in 'iu') and any(sylls[-j].startswith(c) for c in 'aeo')) or
                     (j < len(sylls) - 1 and any(syll.startswith(c) for c in 'iu') and any(sylls[-j-2].endswith(c) for c in 'aeo'))))
            ):
                sylls[-j - 1] = accent(syll.replace('ˈ', ''))
            else:
                sylls[-j - 1] = syll.replace('ˈ', '')
            break
    return ''.join(sylls)


def __yield_sylls(onset: dict, nucleus: dict, coda: dict, start: bool = False) -> Iterator[str]:
    """Does not prune spaces"""
    for o in onset:
        if start and o == 'ɾ':
            continue
        for n in nucleus:
            for c in coda:
                yield '#'.join((o, n, c))


def __yield_words(n: int, onset: dict, nucleus: dict, coda: dict, transitions: dict, start: bool = False) -> Iterator[str]:
    """Does not prune spaces"""
    if n >= 2:
        for syll in __yield_sylls(onset, nucleus, coda, start=start):
            for word in __yield_words(n - 1, onset, nucleus, coda, transitions):
                if syll.split('#')[-1] + '|' + word.split(' ')[0] in transitions:
                    yield syll.replace('#', ' ') + ' . ' + word
    else:
        for syll in __yield_sylls(onset, nucleus, coda, start=start):
            if syll.split('#')[-1] + '|$' in transitions:
                yield syll.replace('#', ' ')


def get_every_word(graph, n_sylls: int, totals: dict, missing_nucleus: list, th: float = default_th, th_trans: float = default_th_trans) -> Iterator[str]:
    graph_pruned = {
        **{key: sorted(k for k, v in graph[key].items() if v/totals[key] >= th)
           for key in ['onset', 'coda']},
        'nucleus': sorted([k for k in graph['nucleus'] if len(k.strip())] + missing_nucleus),
        'transitions': sorted(k for k, v in graph['transitions'].items() if v/totals['transitions'] >= th_trans)
    }
    for w in __yield_words(n_sylls, **graph_pruned, start=True):
        word = w.replace(' ', '')
        if n_sylls > 1:
            for j in range(min(n_sylls, 3)):
                s = word.split('.')
                s[-j-1] = 'ˈ' + s[-j-1]
                yield '.'.join(s)
        else:
            yield word


def load_graph_dict(json_file: Path) -> [dict, dict, list]:
    with open(json_file) as f:
        graph_dict = load(f)

    totals = {k: sum(graph_dict[k].values()) for k in ['onset', 'nucleus', 'coda', 'transitions', 'tonic', 'n_sylls']}
    missing_nucleus = ['i e u', 'u e u', 'u o i', 'u o u']

    return graph_dict, totals, missing_nucleus


def get_random_word(graph, n_sylls: int, totals: dict, th: float = default_th, th_trans: float = default_th_trans) -> str:
    out = []
    for syll in range(n_sylls):
        # onset
        if not syll:
            out += random.choices(*zip(*sorted(
                [(k, v) for k, v in graph['onset'].items() if v / totals['onset'] >= th and k != 'ɾ'],
                key=lambda x: graph['onset'].get(x[0]))))
        else:
            out += random.choices(*zip(*sorted(
                [(k, v / totals['onset'] * sum(graph['transitions'][x] for x in graph['transitions']
                                               if x.split('|')[0] == out[-2] and x.split('|')[1] == k[:1]) / totals['transitions'])
                 for k, v in graph['onset'].items()
                 if v / totals['onset'] >= th
                 and any(graph['transitions'][x] > th_trans for x in graph['transitions']
                         if x.endswith('|' + k[:1]))],
                key=lambda x: graph['onset'].get(x[0]))))

        # nucleus
        out += random.choices(*zip(*sorted(
            [(k, v) for k, v in graph['nucleus'].items() if k],
            key=lambda x: graph['nucleus'].get(x[0]))))

        # coda
        if syll == n_sylls - 1:
            out += random.choices(*zip(*sorted(
                [(k, v / totals['coda'] * sum(graph['transitions'][x] for x in graph['transitions']
                                              if x.split('|')[0] == k and x.split('|')[1] == '$') / totals['transitions'])
                 for k, v in graph['coda'].items()
                 if v / totals['coda'] >= th
                 and graph['transitions'].get(f'{k}|$', 0) / totals['transitions'] >= th_trans],
                key=lambda x: graph['coda'].get(x[0]))))
        else:
            out += random.choices(*zip(*sorted(
                [(k, v) for k, v in graph['coda'].items() if v / totals['coda'] >= th
                 and any(graph['transitions'][x] > th_trans for x in graph['transitions']
                         if x.startswith(k+'|') and not x.endswith('|$'))],
                key=lambda x: graph['coda'].get(x[0]))))
        out.append('.')
    out = ' '.join([k for k in out[:-1] if k.strip()]).split(' . ')
    tonic = min(int(random.choices(*zip(*sorted(
                    [(k, v) for k, v in graph['tonic'].items() if k],
                    key=lambda x: graph['tonic'].get(x[0]))))[0]), n_sylls - 1)
    out[-tonic-1] = 'ˈ' + out[-tonic-1]
    return ' . '.join(out).strip()


def __add_temp_to_distribution(values: List[int], temperature: float) -> np.array:
    """Modifies the distribution of a dictionary by using a temperature value"""
    if temperature <= 0:
        return np.array([1 if v == max(values) else 0 for v in values])
    return np.power(values, 1 / temperature)


def get_random_word_temp(graph, n_sylls: int, totals: dict, th: float = default_th, th_trans: float = default_th_trans, temperature: float = 1.) -> str:
    """Temperature adds randomness to the selection of the syllables"""
    out = []
    for syll in range(n_sylls):
        # onset
        if not syll:
            phones = [k for k, v in graph['onset'].items() if v / totals['onset'] >= th and k != 'ɾ']
            values = __add_temp_to_distribution([graph['onset'][k] for k in phones], temperature)
            out += random.choices(phones, values)
        else:
            phones = [k for k, v in graph['onset'].items() if v / totals['onset'] >= th and any(
                graph['transitions'][x] >= th_trans for x in graph['transitions'] if x.endswith('|' + k.split(' ')[0]))]
            values = __add_temp_to_distribution([
                graph['onset'][k] / totals['onset'] * sum(graph['transitions'][x] for x in graph['transitions']
                                                          if x.split('|')[0] == out[-2] and x.split('|')[1] == k.split(' ')[0])
                / totals['transitions'] for k in phones], temperature)
            out += random.choices(phones, values)

        # nucleus
        phones = [k for k, v in graph['nucleus'].items() if k]
        values = __add_temp_to_distribution([graph['nucleus'][k] for k in phones], temperature)
        out += random.choices(phones, values)

        # coda
        if syll == n_sylls - 1:
            phones = [k for k, v in graph['coda'].items() if v / totals['coda'] >= th and
                      graph['transitions'].get(f'{k}|$', 0) / totals['transitions'] >= th_trans]
            values = __add_temp_to_distribution([
                graph['coda'][k] / totals['coda'] * graph['transitions'].get(f'{k}|$', 0) / totals['transitions']
                for k in phones], temperature)
            out += random.choices(phones, values)
        else:
            phones = [k for k, v in graph['coda'].items() if v / totals['coda'] >= th and any(
                graph['transitions'][x] >= th_trans for x in graph['transitions'] if x.startswith(k + '|') and not x.endswith('|$'))]
            values = __add_temp_to_distribution([
                graph['coda'][k] / totals['coda'] * sum(graph['transitions'][x] for x in graph['transitions']
                                                        if x.startswith(k + '|') and not x.endswith('|$'))
                / totals['transitions'] for k in phones], temperature)
            out += random.choices(phones, values)
        out.append('.')
    out = ' '.join([k for k in out[:-1] if k.strip()]).split(' . ')
    sylls = list(range(n_sylls))
    values = __add_temp_to_distribution([graph['tonic'].get(str(j), 1) for j in sylls], temperature)
    tonic = min(int(random.choices(sylls, values)[0]), n_sylls - 1)
    out[-tonic-1] = 'ˈ' + out[-tonic-1]
    return ' . '.join(out).strip()

