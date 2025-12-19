# synth-eml-generator
Synthetic .eml file generator for testing purposes

## Użycie szablonu

Można dostarczyć gotową treść wiadomości w pliku JSON przekazując parametr `-t`/`--template`:

```json
{
  "subject": "Przykładowy tytuł",
  "text": "Treść tekstowa",
  "html": "<p>Treść HTML</p>"
}
```

Uruchomienie z szablonem:

```bash
python src/main.py -t template.json
```

# Dostępne datasety
## simple
Proste, poprawne i niestanonwiące zagrożenia wiadomości bez linków i załaczników.

## korpo
Stylizowane na wiadomość wewnątrzkorporacyjne.