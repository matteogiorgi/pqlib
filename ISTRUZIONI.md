# Istruzioni repo

Le intenzioni di questo repository sono quelle di creare una libreria che gestisca le priority-queue in diverse modalità:

- heap binari;
- heap di Fibonacci;
- heap di Fibonacci revisited (qui chiamati heap di Kaplan);
- randomized skiplist;
- deterministic skiplist;
- chunked skiplist;

e lascia spazio ad altre implementazioni future che sfruttano altre strutture dati.




## Tassonomia

La seguente tassonomia serve per chiarire cosa deve essere implementato, in realtà sono tutte implementazioni concrete della stessa API pubblica priority-queue:

- ADT pubblico:
    + priority_queue
- famiglie implementative:
    + heaps/
    + skiplists/
- implementazioni concrete:
    + binary_heap
    + fibonacci_heap
    + kaplan_heap
    + randomized_skiplist
    + deterministic_skiplist
    + chunked_skiplist




## Note architetturali

- esiste una sola API astratta pubblica: priority_queue;
- le famiglie heaps/ e skiplists/ sono solo categorie organizzative;
- ogni implementazione concreta fornisce direttamente la vtable della priority_queue;
- non sono previste vtable intermedie per heap o skiplist, salvo necessità future.




## Implementazione codice

Si richiede che il codice abbia le seguenti caratteristiche:

- deve essere implementato interamente in C99 (per avere massima portabilità);
- deve essere strutturato in modo modulare, separando interfaccia e implementazione delle strutture dati;
- ogni priority-queue sarà esposta tramite un’API astratta comune, mentre le diverse varianti concrete (ad esempio implementazioni basate su heap, skip-list o altre strutture dati) forniranno implementazioni distinte della stessa interfaccia logica;
- l’organizzazione del codice ricalca il modello tipico dei linguaggi object-oriented come Java o Scala, ma adattato idiomaticamente al C.




## Operazioni

Un primo set di operazioni delle priority-queue è il seguente:

- create;
- destroy;
- push;
- peek;
- pop;
- size;
- empty.

Altre operazioni più complesse da implementare in un secondo momento sono le seguenti:

- decrease_key;
- remove;
- contains.




# Sviluppo repo

Le seguenti sono le due fasi di sviluppo del repository, con un focus iniziale sulla validazione delle idee di predizione in Python prima di toccare la C API.




## Fase 1: esperimenti Python senza toccare la C API

Prima validiamo che le predizioni abbiano senso.
Aggiungiamo in `tests/learning_augmented_priority_queue.py` funzioni per Dijkstra con trace:

```
dijkstra_with_trace(graph, source, implementation="binary_heap")
```

che ritorna:

```
{
    "distances": ...,
    "extraction_order": ...,
    "inserted_keys": ...,
    "push_trace": ...,
    "stats": {
        "pushes": ...,
        "pops": ...,
        "stale_pops": ...,
        "extractions": ...,
        "reached_nodes": ...
    }
}
```

Poi aggiungiamo predittori:
- `build_node_rank_predictor(previous_extraction_order)`
- `build_key_rank_predictor(previous_inserted_keys)`

Per usare dataset reali di shortest path in formato DIMACS, aggiungiamo anche
un parser riusabile:

- `load_dimacs_graph(path)`

Il parser deve leggere file `.gr` con righe `c`, `p sp <nodes> <arcs>` e
`a <tail> <head> <weight>`, come i grafi stradali del 9th DIMACS Challenge.
La rappresentazione in memoria dei grafi DIMACS deve essere CSR, usando `array`
della standard library per ridurre l'overhead sui grafi grandi.
I test automatici devono usare fixture piccole; grafi grandi come
`graphs/dimacs/USA-road-d.NY.gr` sono destinati a esperimenti o benchmark
manuali.

E testiamo:
1. Dijkstra produce distanze corrette;
2. una run precedente genera predizioni;
3. le predizioni hanno errori misurabili;
4. le predizioni non rompono la correttezza perché la C queue resta il backend reale.

Per completare questa fase, aggiungiamo anche uno script manuale in
`experiments/road_network_experiment.py` che:

- usa davvero un grafo DIMACS come `graphs/dimacs/USA-road-d.NY.gr`;
- esegue Dijkstra da più sorgenti;
- usa ogni run per predire la successiva;
- confronta predizioni node-rank e key-rank;
- stampa statistiche aggregate su errori di predizione, push, pop, stale entries
  e nodi raggiunti.

Questo ci dà dati concreti.




## Fase 2: hint opzionale nella C API

Solo dopo aggiungiamo:

```
int priority_queue_push_with_hint(
    struct priority_queue *queue,
    void *item,
    const void *hint
);
```

All’inizio ogni backend può implementarla come `return priority_queue_push(queue, item);`
Poi aggiorniamo il binding Python con qualcosa tipo:
    - `queue.push(item, hint=...)`
    - o una funzione separata: `queue.push_with_hint(item, hint)`

Io preferirei `push_with_hint` separata, perché rende esplicito che stai usando una feature sperimentale.
