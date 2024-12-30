from json import dump
from pathlib import Path
from typing import List


def onset_nucleus_coda(phones: List[str]) -> [List[str], List[str], List[str]]:
    out = [], [], []
    for ph in phones:
        if ph in 'aeiou':
            out[1].append(ph)
        elif out[1]:
            out[2].append(ph)
        else:
            out[0].append(ph)
    return tuple(map(lambda x: ' '.join(x), out))


if __name__ == '__main__':
    from argparse import ArgumentParser

    p = ArgumentParser()

    p.add_argument('-i', '--input', type=Path, required=True)
    p.add_argument('-o', '--output', type=Path, required=True)
    p.add_argument('-s', '--sep', default=' ')

    args = p.parse_args()

    dicts = {}, {}, {}, {}, {}, {}
    endings = {'agudas': {}, 'llanas': {}}
    with open(args.input, 'r', encoding='utf8') as f_in:
        for line in f_in:
            if not line.strip():
                continue
            _, s = line.strip().split('\t')
            s = s.replace(' ˈ', ' . ˈ')
            s = s.replace(' ˌ', ' . ')
            s = s.replace('ˌ', '')
            prev = None
            for syll in s.replace('ˈ', '').split(' . '):
                tups = onset_nucleus_coda(syll.split())
                for i in range(3):
                    if tups[i] not in dicts[i]:
                        dicts[i][tups[i]] = 1
                    else:
                        dicts[i][tups[i]] += 1
                if prev is not None:
                    transition = f'{prev}|' + tups[0].split(' ')[0]
                    if transition not in dicts[3]:
                        dicts[3][transition] = 1
                    else:
                        dicts[3][transition] += 1
                prev = tups[-1]
            transition = f'{prev}|$'
            if transition not in dicts[3]:
                dicts[3][transition] = 1
            else:
                dicts[3][transition] += 1
            sylls = s.split(' . ')
            for j, syll in enumerate(reversed(sylls)):
                if 'ˈ' in syll:
                    if j > 2:
                        print(s)
                    if j not in dicts[4]:
                        dicts[4][j] = 1
                    else:
                        dicts[4][j] += 1
                    *_, coda = onset_nucleus_coda(sylls[-1].split())
                    if j == 0:
                        if coda not in endings['agudas']:
                            endings['agudas'][coda] = 1
                        else:
                            endings['agudas'][coda] += 1
                    elif j == 1:
                        if coda not in endings['llanas']:
                            endings['llanas'][coda] = 1
                        else:
                            endings['llanas'][coda] += 1
            n_sylls = len(sylls)
            if n_sylls not in dicts[5]:
                dicts[5][n_sylls] = 1
            else:
                dicts[5][n_sylls] += 1

    with open(args.output, 'w') as f_out:
        dump({'onset': dicts[0], 'nucleus': dicts[1], 'coda': dicts[2], 'transitions': dicts[3], 'tonic': dicts[4],
              'n_sylls': dicts[5], 'endings': endings},
             f_out, indent=2, sort_keys=True)
