# Oppgave 05

## Krav -> hvor i prosjektet

- `Array med objekter` -> Dataen ligger i `xenopedia.json`, og blir lest inn i `script.js` med `fetch()` og `response.json()`.
- `Vise data på nettsiden` -> Dataen blir sendt til `renderXenopedia()` i `script.js`, som viser kortene i `section.xenopedia-grid` i `xenopedia.html`.
- `Hvert objekt som eget kort` -> Funksjonen `createXenoCard()` i `script.js` lager ett kort per objekt.
- `Semantisk HTML` -> Strukturen bruker `main`, `header`, `section`, `article` og `footer` i `xenopedia.html` og `script.js`.
- `JavaScript DOM` -> Kortene blir laget med `document.createElement()`, fylt med innhold og satt inn i DOM i `script.js`.
- `Minst fire kort med flere datapunkter` -> `xenopedia.json` inneholder mange objekter, og hvert kort viser `navn`, `beskrivelse`, `trusler` og `bilde`.
- `CSS styling` -> Kortlayout, spacing, border og visuell struktur er laget i `styles.css`.
- `Responsivt design` -> Media queries for mobil og desktop ligger i `styles.css`.
- `Enkel feilhåndtering` -> Hvis dataen ikke kan lastes eller ikke er gyldig, vises en melding på siden gjennom `showXenopediaMessage()` i `script.js`.