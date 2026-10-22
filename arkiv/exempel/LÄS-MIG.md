# Arkiv: Exempelsidan och exempelbutiken Norrsund Hem

Exempelsidan togs bort från sajten men finns sparad här, och hela sajten med exemplet
finns kvar i git-taggen `arkiv-exempel`.

## Innehåll

| Fil eller mapp | Vad det är | Ska tillbaka till |
|---|---|---|
| `src-sv/exempel.html` | Exempelsidan på svenska | `src/sv/exempel.html` |
| `src-en/exempel.html` | Exempelsidan på engelska | `src/en/exempel.html` |
| `norrsund/` | Exempelbutiken Norrsund Hem | `exempel/norrsund/` |
| `assets/` | Skärmbilder till genomgången | `assets/exempel/` |
| `startsida-sektion-sv.html` / `-en.html` | Sektionen på startsidan | Före `<!-- Så går det till -->` / `<!-- How it works -->` i `src/*/index.html` |
| `build-page-entry.txt` | Sidans rad i `PAGES` | Före `"livesandning"` i `tools/build.py` |

## Sätta tillbaka

1. Flytta filerna enligt tabellen ovan.
2. I `tools/build.py`:
   - lägg tillbaka raden från `build-page-entry.txt` i `PAGES`,
   - lägg `"exempel"` efter `"webbtjanster"` i `NAV`,
   - lägg `"exempel": "Exempel"` i `NAV_LABEL` och i `labels` (`"Examples"` på engelska),
   - lägg `<li><a href="{p}exempel.html">Exempel</a></li>` efter Hemsidor i sidfoten.
3. Kör `python tools/build.py`.

Stilarna (`.showcase`, `.walk`, `.under`, `.ds`, `.ex-home` m.fl.) ligger kvar i `css/v3.css`.
