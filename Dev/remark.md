# Remark til Oppgave 05

- Oppgave 05 er implementert i det eksisterende XenoLogic-prosjektet i stedet for som et eget, separat prosjekt.
- Den spesifikke løsningen er samlet på Xenopedia-siden, der dataen vises som kort med JavaScript DOM-logikk, responsiv CSS og enkel feilhåndtering.
- For å passe inn i prosjektstrukturen er oppgavedataen lagt i en lokal JSON-fil, men den fungerer som prosjektets egen datasamling med objekter for denne oppgaven.

## Krav -> hvor i prosjektet

- `Array med objekter` -> Oppgavedataen er laget som en egen lokal datasamling med objekter i `xenopedia.json`, og blir lest inn i `script.js` med `fetch()` og `response.json()`.
- `Vise data på nettsiden` -> Dataen blir sendt til `renderXenopedia()` i `script.js`, som viser kortene i `section.xenopedia-grid` i `xenopedia.html`.
- `Hvert objekt som eget kort` -> Funksjonen `createXenoCard()` i `script.js` lager ett kort per objekt.
- `Semantisk HTML` -> Strukturen bruker `main`, `header`, `section`, `article` og `footer` i `xenopedia.html` og `script.js`.
- `JavaScript DOM` -> Kortene blir laget med `document.createElement()`, fylt med innhold og satt inn i DOM i `script.js`.
- `Minst fire kort med flere datapunkter` -> `xenopedia.json` inneholder mange objekter, og hvert kort viser `navn`, `beskrivelse`, `trusler` og `bilde`.
- `CSS styling` -> Kortlayout, spacing, border og visuell struktur er laget i `styles.css`.
- `Hover-/designeffekt` -> Kortene har også en egen 3D-effekt ved hover som et bevisst designvalg. Denne er laget med `attachXenoCardTilt()` i `script.js` og transform-/hover-stiler i `styles.css`.
- `Responsivt design` -> Media queries for mobil og desktop ligger i `styles.css`.
- `Enkel feilhåndtering` -> Hvis dataen ikke kan lastes eller ikke er gyldig, vises en melding på siden gjennom `showXenopediaMessage()` i `script.js`.