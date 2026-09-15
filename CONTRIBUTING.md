# Contribuire a Wall Damage Analyzer

Grazie per l'interesse nel contribuire! 🎉

## Come Contribuire

### 1. Segnalare Bug
- Usa GitHub Issues
- Includi: descrizione, passi per riprodurre, comportamento atteso vs osservato
- Allega screenshot/log se rilevante

### 2. Suggerire Funzionalità
- Apri una Discussion
- Descrivi il caso d'uso
- Fornisci esempi di utilizzo

### 3. Inviare Pull Requests
- Crea un branch: `git checkout -b feature/nome-feature`
- Commita le tue modifiche: `git commit -m 'feat: descrizione'`
- Push: `git push origin feature/nome-feature`
- Apri una PR

## Standard di Codice

- **Linguaggio**: Python 3.10+
- **Style Guide**: PEP 8
- **Formatter**: Black
- **Linter**: Pylint/Flake8
- **Type Hints**: Fortemente incoraggiati

### Eseguire i Controlli di Qualità

```bash
# Formattazione
black src/

# Linting
flake8 src/
pylint src/

# Type checking
mypy src/

# Test
pytest tests/
```

## Struttura del Codice

```
src/
├── image_processor/    # Caricamento e preprocessing
├── analysis/          # Logica di analisi
├── database/          # Gestione database
├── api/              # Endpoint API
└── utils/            # Funzioni di utilità
```

## Git Workflow

1. Fai fork del repository
2. Crea un branch feature: `git checkout -b feature/nome`
3. Commit: `git commit -am 'feat: descrizione'`
4. Push: `git push origin feature/nome`
5. Apri una Pull Request

## Messaggi di Commit

Usa il formato Conventional Commits:

- `feat:` per nuove funzionalità
- `fix:` per correzioni di bug
- `docs:` per documentazione
- `style:` per formattazione
- `refactor:` per refactoring
- `test:` per test
- `chore:` per manutenzione

Esempio: `feat: add damage detection algorithm`

## Processo di Review

- Tutti i PR devono essere approvati
- CI/CD deve passare
- Minimo 90% code coverage per i test

## Licenza

Contribuendo, accetti che i tuoi contributi siano disponibili sotto licenza MIT.
