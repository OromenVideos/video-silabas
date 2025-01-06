# Sílabas

Código para generar palabras aleatorias en castellano

## Invitación al servidor de Discord

[![Discord Server Invite](https://invite.casperiv.dev?inviteCode=vY5NAcvEqR)](https://discord.gg/vY5NAcvEqR)

## Vídeo
[![YouTube](http://i.ytimg.com/vi/bkOiHx0NIgo/hqdefault.jpg)](https://www.youtube.com/watch?v=bkOiHx0NIgo)


## Extraer palabras de [Wiktionary](https://en.wiktionary.org/wiki/Wiktionary:Main_Page)

Se proporciona en el repositorio el fichero `sylls.json` con las estadísticas de cada fonema.
En el caso de querer generar un nuevo fichero, se deberá extraer la información de fonemas utilizando el repositorio oficial de [wikipron](https://github.com/CUNY-CL/wikipron).
Recuerda guardar también la información de _stress_ (la sílaba tónica).

### Limpiador de pronunciaciones

Para limpiar la pronunciación obtenida por wikipron:

```bash
python3 clean_spa.py -i wikipron_scraped_spa_stress.tsv -o wikipron_scraped_spa_stress_parsed.tsv
```

### Obtener estadísticas

Finalmente, para obtener el fichero `sylls.json`:

```bash
python3 create_transducer.py -i wikipron_scraped_spa_stress_parsed.tsv -o sylls.json
```

## Generación de palabras 

Para imprimir por pantalla el número de palabras totales utilizando el fichero `sylls.json`:

```bash
python3 get_total_words.py -s $ruta_a_sylls.json -n $numero_de_silabas 
```

Para cambiar los valores de frecuencia máxima para fonemas o para transiciones coda-ataque se pueden utilizar los parámetros `--th` y `--th-trans` respectivamente.

### Generación de TODAS las palabras

**Atención, puede tardar mucho tiempo y crear archivos muy pesados**

Simplemente, se añade el parámetro `-o` con la ruta al fichero de salida: 

```bash
python3 get_total_words.py -s $ruta_a_sylls.json -n $numero_de_silabas -o $fichero_de_salida
```

Se puede añadir el parámetro `-v` para que imprima el progreso por pantalla (requiere [`tqdm`](https://tqdm.github.io))

Para cambiar los valores de frecuencia máxima para fonemas o para transiciones coda-ataque se pueden utilizar los parámetros `--th` y `--th-trans` respectivamente.

### Generación de palabras aleatorias

Para imprimir por pantalla un número concreto de palabras aleatorias utilizando el fichero `sylls.json`:

```bash
python3 get_random_words.py -s $ruta_a_sylls.json -n $numero_de_silabas -k $numero_de_palabras
```

Se puede añadir el parámetro `-t` si se quiere utilizar temperatura:

```bash
python3 get_random_words.py -s $ruta_a_sylls.json -n $numero_de_silabas -k $numero_de_palabras -t $temperatura
```

Para cambiar los valores de frecuencia máxima para fonemas o para transiciones coda-ataque se pueden utilizar los parámetros `--th` y `--th-trans` respectivamente.
