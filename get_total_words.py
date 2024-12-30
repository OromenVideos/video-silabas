from pathlib import Path
from time import time

from sylls.utils import default_th, default_th_trans, load_graph_dict, get_total_words, get_every_word, \
    phones_to_graphemes, get_logprob


if __name__ == '__main__':
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.add_argument('-n', '--n-sylls', type=int,
                        help='Número de sílabas a calcular')
    parser.add_argument('-s', '--sylls-json', type=Path,
                        help='Fichero `sylls.json`')
    parser.add_argument('-o', '--output', type=Path,
                        help='Fichero de salida. Si no se proporciona, indica el número de posibles palabras')
    parser.add_argument('--th', default=default_th, type=float,
                        help=f'Mínima frecuencia de aparición de fonema. Por defecto {default_th:.2%}')
    parser.add_argument('--th-trans', default=default_th_trans, type=float,
                        help=f'Mínima frecuencia de transición coda-ataque. Por defecto {default_th_trans:.2%}')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Imprime el progreso por pantalla (requiere tqdm)')
    
    args = parser.parse_args()

    if args.verbose:
        from tqdm import tqdm

    graph_dict, totals, missing_nucleus = load_graph_dict(args.sylls_json)
    
    if args.output is None:
        print(f'{get_total_words(graph_dict, args.n_sylls, totals, th=args.th, th_trans=args.th_trans, verbose=args.verbose):_}'.replace('_', ' '),
              f'palabras de {args.n_sylls} sílaba' + ('s' if args.n_sylls != 1 else ''))

    else:
        start = time()
        if args.verbose:
            print(f'Calculando palabras de {args.n_sylls} sílaba' + ('s' if args.n_sylls != 1 else ''))
            pbar = tqdm(total=get_total_words(graph_dict, args.n_sylls, totals, th=args.th, th_trans=args.th_trans, verbose=args.verbose))
        with open(args.output, 'w', encoding='utf8') as f:
            for ph in get_every_word(graph_dict, args.n_sylls, totals, missing_nucleus, th=args.th, th_trans=args.th_trans):
                print(phones_to_graphemes(ph), ph, round(get_logprob(graph_dict, ph, totals), 2), sep='\t', file=f)
                if args.verbose:
                    pbar.update()
        if args.verbose:
            tot = pbar.n
            pbar.close()
            print(f'Ha tardado {time()-start:.2f} segundos en calcular {tot} palabras')
