import re

from pathlib import Path


remove = {'ə', 'ɛː', 'aː', 'ɪ', 'ɹ', 'ɸ', 'h', 'ˈʃ', ' ʃ', 'ʒ', 's t', 's p', 's k'}

diacritics = '\u031d\u031e\u031f\u032a\u032c\u032f\u0361'

clean = [
    {
        'ã': 'a',
        'β': 'b',
        'ð': 'd',
        'ẽ': 'e',
        'ɣ': 'g',
        'ɡ': 'g',
        'lʲ': 'l',
        'ĩ': 'i',
        'j': 'i',
        'ɱ': 'n',
        'ŋ': 'n',
        'nʲ': 'n',
        'ɲ .': 'n .',
        'õ': 'o',
        'ũ': 'u',
        'w': 'u',
        'v': 'f',
        'z': 's',
        'ɟʝ': 'ʝ',
    },
    {
        '. d ʝ': 'd . ʝ',
        re.compile(r'g s( [ˈˌ.]|$)'): r'k s\1',
        re.compile(r'g ([ˈˌ]|\. )s'): r'k \1s',
    }
]

choose = ['θʎ', 'ʝ']


def clean_phones(word: str, phones: str) -> str:
    def __process_clean(key, value):
        if isinstance(key, str):
            return out.replace(key, value)
        else:
            return re.sub(key, value, out)      
    out = phones
    for c in diacritics:
        out = out.replace(c, '')
    for d in clean:
        for c in d:
            if isinstance(d[c], str):
                out = __process_clean(c, d[c])
            elif (c[0] == '^' and not re.search(c[1:], word)) or (c[0] != '^' and c in word):
                for k in d[c]:
                    out = __process_clean(k, d[c][k])
    return out


if __name__ == '__main__':
    from argparse import ArgumentParser

    p = ArgumentParser()
    p.add_argument('-i', '--input', type=Path)
    p.add_argument('-o', '--output', type=Path)

    args = p.parse_args()

    prev = None
    same = set()

    with open(args.input, 'r', encoding='utf8') as f_in, open(args.output, 'w', encoding='utf8') as f_out:
        for line in f_in:
            if not line.strip():
                continue
            w, ph = line.strip().split('\t')
            if any(c in ph for c in remove) or ph.startswith('ʃ') or (len(w) == 1 and w not in 'aeiouy'):
                continue
            ph = clean_phones(w, ph)
            if w == prev:
                same.add(ph)
                continue
            if len(same) > 1:
                d = {k: sum((int(c in k)/(i+1) for i in range(len(choose)) for c in choose[i])) for k in same}
                same = {k for k in same if d[k] == max(d.values())}
            for k in same:
                print(prev, k, sep='\t', file=f_out)
            prev = w
            same = {ph}
        if len(same) > 1:
            d = {k: sum((int(c in k)/(i+1) for i in range(len(choose)) for c in choose[i])) for k in same}
            same = {k for k in same if d[k] == max(d.values())}
        for k in same:
            print(prev, k, sep='\t', file=f_out)
