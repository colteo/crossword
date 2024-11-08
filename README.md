# Crossword Generator

Un generatore di cruciverba flessibile e configurabile che supporta diversi tipi di schemi e algoritmi di generazione. Il sistema può generare sia cruciverba standard che cruciverba con parola nascosta, utilizzando un database MySQL per le parole e le definizioni.

## 🎯 Caratteristiche

- **Multiple modalità di generazione:**
  - Cruciverba standard (3 tipi diversi di layout)
  - Cruciverba con parola nascosta
- **Configurazione flessibile:**
  - Dimensione griglia personalizzabile
  - Dimensione celle regolabile
  - Parametri specifici per ogni tipo di cruciverba
- **Output multiplo:**
  - File JSON per integrazione con altre applicazioni
  - File di testo per visualizzazione umana
  - Log dettagliati per debugging
- **Gestione robusta degli errori**
- **Sistema di tentativi multipli per garantire la generazione**

## 📋 Requisiti

- Python 3.x
- MySQL Server
- Pacchetti Python:
  ```
  mysql-connector-python
  ```

## 💾 Configurazione Database

1. Creare un database MySQL:
```sql
CREATE DATABASE crossword;
```

2. Creare un utente e assegnare i permessi:
```sql
CREATE USER 'crossword'@'localhost' IDENTIFIED BY 'crossword';
GRANT ALL PRIVILEGES ON crossword.* TO 'crossword'@'localhost';
```

3. Creare la tabella necessaria:
```sql
CREATE TABLE crossword_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    solution VARCHAR(15) NOT NULL,
    clue TEXT NOT NULL,
    word_pattern VARCHAR(50),
    num_words INT DEFAULT 1
);
```

## 🚀 Installazione

1. Clonare il repository:
```bash
git clone <repository-url>
cd crossword-generator
```

2. Installare le dipendenze:
```bash
pip install -r requirements.txt
```

3. Verificare la configurazione del database nel file `main.py`

## 💻 Utilizzo

### Comando Base
```bash
python main.py -t <tipo> -s <dimensione>
```

### Tipi di Cruciverba Disponibili
- `type_a`: Layout orizzontale centrico
- `type_b`: Layout verticale centrico
- `type_c`: Layout misto
- `hidden`: Cruciverba con parola nascosta

### Esempi di Utilizzo

1. Generare un cruciverba standard di tipo A:
```bash
python main.py -t type_a -s 15 --cell-size 75
```

2. Generare un cruciverba con parola nascosta:
```bash
python main.py -t hidden --hidden-length 8 --min-words 6 --max-words 10
```

3. Generare un cruciverba con output verboso:
```bash
python main.py -t type_b -s 20 -v
```

### Opzioni Disponibili
```
-t, --type          Tipo di cruciverba (required)
-s, --size          Dimensione della griglia (default: 15)
--cell-size         Dimensione delle celle in pixel (default: 75)
--max-attempts      Numero massimo di tentativi (default: 3)
--hidden-length     Lunghezza della parola nascosta (per tipo 'hidden')
--min-words         Numero minimo di parole intersecanti
--max-words         Numero massimo di parole intersecanti
-v, --verbose       Output verboso
```

## 📂 Struttura del Progetto

```
crossword-generator/
├── base/
│   ├── base_generator.py    # Classe base per i generatori
│   ├── word.py             # Classe per la gestione delle parole
│   └── hidden_word_generator.py
├── generators/
│   ├── type_a.py           # Implementazione tipo A
│   ├── type_b.py           # Implementazione tipo B
│   ├── type_c.py           # Implementazione tipo C
│   └── hidden_word_a.py    # Implementazione parola nascosta
├── utils/
│   ├── db_utils.py         # Utility database
│   └── grid_utils.py       # Utility griglia
└── main.py                 # Script principale
```

## 📤 Output

Il generatore crea una directory di output per ogni cruciverba generato, contenente:
- `crossword.json`: Rappresentazione JSON completa
- `crossword.txt`: Versione leggibile del cruciverba
- `crossword.log`: Log dettagliato della generazione

### Formato JSON
```json
{
    "metadata": {
        "guid": "uuid",
        "timestamp": "YYYYMMDD-HHMMSS",
        "grid_size": 15,
        "cell_size": 75
    },
    "grid": [...],
    "words": [...]
}
```

## 🤝 Contribuire

1. Fork del repository
2. Creare un branch per la feature (`git checkout -b feature/nome-feature`)
3. Commit delle modifiche (`git commit -am 'Aggiunta nuova feature'`)
4. Push al branch (`git push origin feature/nome-feature`)
5. Creare una Pull Request

## 🐛 Segnalazione Bug

Per segnalare bug o richiedere nuove funzionalità, utilizzare il sistema di Issue di GitHub.

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedere il file `LICENSE` per i dettagli.

## Esempi Base per Cruciverba Standard Tipo A (Layout Orizzontale)
### ------------------------------------------------------
### Dimensione standard
python main.py -t type_a -s 15

### Dimensione personalizzata piccola
python main.py -t type_a -s 10 --cell-size 50

### Dimensione grande con celle grandi
python main.py -t type_a -s 20 --cell-size 100

### Con output verboso per debugging
python main.py -t type_a -s 15 -v

### Con numero massimo di tentativi personalizzato
python main.py -t type_a -s 15 --max-attempts 5


## Esempi per Cruciverba Standard Tipo B (Layout Verticale)
### ------------------------------------------------------
### Configurazione base
python main.py -t type_b -s 15

### Versione compatta
python main.py -t type_b -s 12 --cell-size 60

### Versione grande con debugging
python main.py -t type_b -s 25 -v --max-attempts 4

### Con celle molto piccole per display compatti
python main.py -t type_b -s 15 --cell-size 40


## Esempi per Cruciverba Standard Tipo C (Layout Misto)
### ------------------------------------------------------
### Configurazione standard
python main.py -t type_c -s 15

### Versione ottimizzata per stampa
python main.py -t type_c -s 15 --cell-size 90

### Versione grande con molti tentativi
python main.py -t type_c -s 30 --max-attempts 6 -v

### Versione compatta per test
python main.py -t type_c -s 8 --cell-size 45


## Esempi per Cruciverba con Parola Nascosta
### ------------------------------------------------------
### Configurazione base
python main.py -t hidden --hidden-length 8 --min-words 6 --max-words 10

### Versione con molte parole intersecanti
python main.py -t hidden --hidden-length 10 --min-words 8 --max-words 15

### Versione compatta
python main.py -t hidden --hidden-length 6 --min-words 4 --max-words 8 --cell-size 50

### Versione grande con debugging
python main.py -t hidden --hidden-length 12 --min-words 10 --max-words 20 -v

### Versione ottimizzata per difficoltà media
python main.py -t hidden --hidden-length 8 --min-words 7 --max-words 12 --cell-size 80


## Esempi con Combinazioni di Parametri Avanzate
### ------------------------------------------------------
### Tipo A con tutti i parametri personalizzati
python main.py -t type_a -s 18 --cell-size 85 --max-attempts 4 -v

### Tipo B ottimizzato per performance
python main.py -t type_b -s 15 --cell-size 70 --max-attempts 2

### Tipo C per grandi display
python main.py -t type_c -s 25 --cell-size 120 --max-attempts 5 -v

### Parola nascosta complessa
python main.py -t hidden --hidden-length 15 --min-words 12 --max-words 25 --cell-size 95 -v --max-attempts 8


## Esempi per Casi Speciali
### ------------------------------------------------------
### Generazione rapida per test
python main.py -t type_a -s 8 --cell-size 40 --max-attempts 1

### Generazione ottimizzata per stampa professionale
python main.py -t type_b -s 20 --cell-size 150 --max-attempts 3

### Generazione per display ad alta risoluzione
python main.py -t type_c -s 30 --cell-size 200 -v

### Parola nascosta per bambini (più semplice)
python main.py -t hidden --hidden-length 5 --min-words 3 --max-words 6 --cell-size 100