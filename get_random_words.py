from pathlib import Path

from sylls.utils import get_random_word, get_random_word_temp, phones_to_graphemes, get_logprob, default_th, default_th_trans, load_graph_dict


if __name__ == '__main__':
    
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.add_argument('-n', '--n-sylls', type=int, 
                        help='Número de sílabas de la palabra')
    parser.add_argument('-s', '--sylls-json', type=Path,
                        help='Fichero `sylls.json`')
    parser.add_argument('-k', '--n-words', type=int,
                        help='Número de palabras a generar')
    parser.add_argument('-t', '--temperature', type=float,
                        help=f'Valor de temperatura. Si no se proporciona, se presupone p(s) = f(s)')
    parser.add_argument('--th', default=default_th, type=float,
                        help=f'Mínima frecuencia de aparición de fonema. Por defecto {default_th:.2%}')
    parser.add_argument('--th-trans', default=default_th_trans, type=float,
                        help=f'Mínima frecuencia de transición coda-ataque. Por defecto {default_th_trans:.2%}')

    args = parser.parse_args()

    graph_dict, totals, missing_nucleus = load_graph_dict(args.sylls_json)

    for i in range(args.n_words):
        if args.temperature is None:
            ph = get_random_word(graph_dict, args.n_sylls, totals, th=args.th, th_trans=args.th_trans)
        else:
            ph = get_random_word_temp(graph_dict, args.n_sylls, totals, th=args.th, th_trans=args.th_trans, temperature=args.temperature)
        print(f'{phones_to_graphemes(ph)} ({ph}) (logprob: {get_logprob(graph_dict, ph, totals):.2f})')
