# XenoLogic – DevPlan MVP UA

## Інтро

### Назва

- `XenoLogic` – основна назва продукту

Alternatives:
- `Lost Signal` – може стати назвою місії, сценарію, модуля або кампанії у Full Product

### Слогани

- `Biology wiggles. Logic remains.`
- `Biologien svinger, logikken består.`

Alternatives:
- Biology wiggles. Logic remains.
- Biology shifts, logic remains.
- Biology drifts, logic remains.

### Опис
- Educational logic quiz with a sci-fi xeno-biology setting.

### Тон

XenoLogic зберігає той самий принцип, що й оригінальний формат на основі тесту Войнаровського: дитина вчить серйозну формальну логіку, дедукцію та розпізнавання хибних висновків не через сухі академічні приклади, а через абсурдний, кумедний і химерний контент, де дивні істоти виконують безглузді дії у контрольовано сюрреалістичному світі; саме цей сильний контраст між суворою логічною структурою і грайливою, майже безсоромно дивною подачею робить навчання живим, запам’ятовуваним і психологічно легшим для дитини.

### Мова MVP

- `English` – primary language for MVP

### Базова теза продукту

`No matter how strange the subject is, logic stays the same.`

### Робоче продуктове формулювання

`XenoLogic is a sci-fi logic training interface where the player analyzes alien field reports and classifies what can be logically concluded.`

---

## Суть продукту

`XenoLogic` – це sci-fi логічний тренажер, де користувач працює з польовими записами про інопланетні форми життя та визначає, що з них логічно випливає.

Освітнє ядро:
- логіка
- inference
- розпізнавання логічних помилок
- уважне читання тверджень
- відокремлення того, що справді випливає, від того, що лише здається правдоподібним

Ігрова оболонка:
- космічні істоти
- xeno-архів
- дослідницька станція
- польові звіти
- signal / terminal / archive aesthetics

Ключовий принцип:
- якими б дивними не були істоти, події або лор, логіка залишається сталою

---

## Продуктова рамка MVP

### Що є метою MVP

Побудувати повноцінний MVP-продукт з реальною логічною системою, але презентувати його в Phase 1 через керований і реалістичний дизайн головної сторінки для `Oppgave 2`.

`XenoLogic MVP` повинен зберегти повне логічне ядро референса `LogikkQuiz`, але бути повністю переналаштованим на alien-only domain.

### У MVP входить

- повна адаптована логічна система з референса `LogikkQuiz`
- усі вже розроблені логічні операції
- повна структура рівнів складності
- повний template-based generation pipeline
- generator-driven архітектура без спрощення основної логіки
- alien-only конфіги для:
	- істот
	- дій
	- властивостей
	- об'єктів взаємодії
	- допоміжних категорій
- 10–15 послідовних питань на сесію
- 3 рівні складності
- текстовий інтерфейс у дусі `LogikkQuiz`, без складного мультимедійного шару

### Що треба адаптувати від референса

- прибрати неінопланетні сутності
- прибрати неінопланетні контексти й дії
- адаптувати vocabulary і tone під англомовний sci-fi стиль
- зберегти логічну точність, але змінити тематичний світ

### Технічні межі для Phase 2

- базовий стек: `HTML`, `CSS`, `JavaScript`;
- layout: `Flexbox` і там, де доречно, `Grid`;
- typography: `Google Fonts`;
- responsive: `media queries` + responsive units;
- deploy: `GitHub` + `Vercel`.

Що свідомо не входить у `Oppgave 03`:

- `React`, `Next.js`, `TypeScript` чи інший framework stack;
- повна багатомовна система;
- повний перенос generator pipeline;
- production-grade application architecture.

---

## Архітектура

### MPA

- вимоги завдання природно лягають на окремі content pages
- quiz flow є послідовним і екранно-орієнтованим
- головна сторінка має бути компактною точкою входу, а не контейнером для всього продукту

### Принцип

- `Homepage` не є довгою scrolling-сторінкою з усім вмістом одразу
- `Homepage` є entry screen
- основний quiz flow живе окремою гілкою сторінок
- додаткові інформаційні сторінки живуть окремо в навігації

### Структурна ієрархія

```text
Homepage
├ XenoLogic Terminal
│  └ Clearance Level ⇒ Quiz Session ⇒ XenoReport
├ Inference Protocols
├ Xenopedia
└ Station Log
```

### Роль сторінок

`Homepage`
- коротка точка входу
- бренд
- тон
- CTA на початок аналізу
- кнопка запуску `XenoLogic Terminal`

`XenoLogic Terminal`
- окрема сторінка, екран основного flow
- дає вибір рівня допуску, а потім запускає quiz flow
- стилістично виглядає як термінал на ксенобіологічній станції

`Clearance Level`
- рівень допуску є diegetic-обгорткою для складності

`Quiz Session`
- основний ланцюг завдань
- орієнтовно 15 окремих сторінок/екранів у flow
- логіка побудови береться з Python-референса

`XenoReport`
- фінальний екран після проходження сесії
- показує результат, точність та інші ключові підсумки

`Inference Protocols`
- одна інформаційна сторінка, пояснює логічні правила й основу аналізу

`Xenopedia`
- окрема сторінка-галерея / архів істот
- одночасно worldbuilding і візуальний шар продукту

`Station Log`
- окрема сторінка для статистики (якщо зробимо систему облікових записів) або для додаткового lore і worldbuilding

### Що цим рішенням уже зафіксовано

- homepage не намагається вмістити весь quiz flow
- вибір складності не показується як головний контент homepage
- quiz session не моделюється як одна довга SPA-сторінка
- продуктова навігація відразу мислиться як набір окремих сторінок

### Робочі назви рівнів допуску
- Clearance Levels:
  - `Observer Clearance` – easy
  - `Analyst Clearance` – standard
  - `Containment Clearance` – hard

---

## Напрям дизайну

### Базовий напрям

- research terminal
- xeno archive
- signal analysis interface

### Візуальний тон

Основний вектор:
- clean research
- signal mystery
- controlled absurdity in content

Не ціль:
- перевантажений кіберпанк
- візуальний хаос
- надмірний glitch
- стерильний безхарактерний sci-fi

### Візуальні мотиви

- thin UI lines
- panel-based layout
- waveform / radar motifs
- restrained glitch details
- archive / scan / signal language

### Layout Principle

- outer page / frame може бути full width
- основний контент homepage не тягнеться на всю ширину
- UI живе в центральному content container приблизно `70-80%` ширини desktop frame
- фон працює як atmosphere layer, а не як основний контентний носій

### Background Direction

- full-width background: зоряне космічне небо
- темна космічна база
- дрібні зірки
- м'які туманні або glow-області
- background не повинен конкурувати з текстом

### Content Separation

- поверх full-width background контент має читатися як окремий керований інтерфейсний модуль
- за потреби під контентом можна використовувати легкий темний overlay або м'яке відділення від фону
- ціль: створити відчуття, що UI існує всередині більшого космічного середовища

### Типографіка

- основний шрифт усього дизайну: `Orbitron`
- джерело: Google Fonts
- використовується як основний display і body font у MVP-дизайні
- візуально підтримує sci-fi terminal tone, але має лишатися читабельним

### Кольорова схема

Основний принцип:
- dark background
- light text
- контраст стриманий, не крикливий
- accent використовується дозовано

#### Base palette

- `Background`: `#0B1020`
- `Surface / Panel`: `#11182B`
- `Primary Text`: `#E8EEF7`
- `Secondary Text`: `#9AA6BF`
- `Accent`: `#6FE7FF`
- `Subtle Border`: `#26324A`

#### Додаткові службові кольори

- `Success / Low Clearance`: `#7EE081`
- `Warning / Mid Clearance`: `#F1C75B`
- `Danger / High Clearance`: `#F06A6A`

#### Розподіл ролей кольору

- `Background` – outer frame, космічне небо, базовий темний фон
- `Surface / Panel` – контентні панелі, terminal surface, блоки інтерфейсу
- `Primary Text` – headline, основний текст, ключові UI-лейбли
- `Secondary Text` – metadata, supporting text, disclaimer text
- `Accent` – CTA, signal details, активні акценти, окремі дрібні підсвітки
- `Subtle Border` – рамки панелей, поділювачі, thin interface lines

#### Принцип використання

- не використовувати чисто чорний фон і чисто білий текст
- не перетворювати сторінку на неоновий sci-fi
- accent має працювати як signal color, а не як основа всієї сторінки
- орієнтовна пропорція: `70%` dark base / `20%` light text and surfaces / `10%` accent and status colors

---

## Сюжетна рамка

На дослідницькій станції збирають записи про невідомі форми життя.
Кожне питання – це фрагмент польового звіту.
Гравець аналізує поведінку істот і визначає, що справді випливає з наявних даних.

### Можливі ролі користувача

- `xeno-analyst`
- `station archivist`
- `signal biologist`
- `containment logic officer`

Поточний пріоритет для MVP:
- `xeno-analyst`

---

## Каркас головної сторінки

Головна сторінка мислиться як компактна entry page без довгого скролу.

Її задача:
- дати перше занурення у світ
- створити інтригу
- передати tone of voice
- направити користувача в `XenoLogic Terminal`

Вона не повинна детально пояснювати всю логіку продукту вже на першому екрані.

### Header

flex row:

- logo label : `AX`  | title image: `XenoLogic` /  `Biology wiggles. Logic remains.` flex column |switch : `EN | UA | NO`


### Navigation Row

flex row:

  `Inference Protocols | Xenopedia | Station Log` 


### Hero

- працює як narrative entry point, не пояснює механіку прямо
- вводить у сюжет і атмосферу, відчуття, що користувач потрапив на дивну дослідницьку станцію
- у фінальному layout мислиться як 2-колонковий блок: текстова колонка + візуальна колонка

flex column з вертикальним ритмом:

#### Вступ

- eyebrow / status line: `AXIOM STATION // ACTIVE SIGNAL WINDOW`
- intro line: `Axiom Station has resumed classified observation across unstable alien sectors.`

#### Опис гри в сюжетній манері

- станція `Axiom Station` досліджує інопланетні форми життя
- спостереження накопичуються у вигляді польових звітів з зондів, телескопів, орбітальних станцій, дронів-дослідників
- мова подачі тримає ігровий вайб і легку дивність

Text:
- paragraph: `From orbital probes to deep-field drones, Axiom Station gathers classified records of species that refuse to behave in reasonable ways.`

#### CTA-секція

- звертання до юзера: "твоя задача як аналітика – зрозуміти логіку поведінки іншоземельних істот"
- запрошення самому переглянути дані спостережень
- зробити логічні висновки
- занести результат у щоденник / звіт ксеноетолога

Text:
- `Your role is not to admire them. Your role is to determine what follows logically from the evidence.`
- `Review the observation logs, isolate the valid conclusion, and file your report before the specimen changes its mind.`

- велика кнопка `Launch XenoLogic Terminal`
- optional secondary microcopy: `Authorized analysts only`

#### Disclaimer

- `Do not mimic observed organism behavior without proper clearance. It can cause unpredictable consequences.`

Альтернативи:
- `All field conclusions remain provisional until verified by logic.`
- `Unauthorized empathy with unknown species is discouraged.`
- `If the organism wiggles first, remain calm.`

#### Візуальна колонка hero

- великий terminal / signal / scan placeholder
- під ним малий додатковий блок `Station Feed`

#### Нижній блок під terminal preview

Цей блок не є важливою інформаційною секцією.

Його роль:
- дати легкий in-world коментар
- підтримати tone of voice
- створити відчуття, що станція жива і постійно щось фіксує
- додати маленький смішний або химерний procedural flavor

Формат блоку:
- label: `Station Feed`
- маленька картинка / snapshot / scan image
- короткий headline
- 1-2 рядки тексту

Функція блоку:
- коротка сюжетна ремарка
- station news
- xeno-observation joke
- маленький procedural output, ніби система згенерувала коментар про дивну поведінку істот

Text placeholder type:
- block label: `Station Feed`
- headline example 01: `Cosmo-flies continue attacks on survey drones`
- text example 01: `For reasons still unclear, the winged lifeforms of Sector XX keep targeting exposed antenna arrays.`
- headline example 02: `Specimen 04 attempted to classify the observer first`
- text example 02: `No consensus has been reached on whether this counts as intelligence, sarcasm, or a territorial reflex.`
- headline example 03: `Three signals were recorded. One was just rude.`
- text example 03: `Field teams confirm that not every transmission from deep space can be described as constructive.`

Принцип:
- блок має бути коротким
- не пояснює механіку
- не дублює CTA
- працює як атмосферний aftertaste під terminal visual


### Footer

Footer має виглядати як офіційно-дивний службовий блок ксенобіологічної станції.

Робочий стиль:
- формально-офіційний
- космічно-бюрократичний
- трохи з'їхавший від довгого контакту з alien biology

#### Вигадані координати / службові дані

flex row з двома колонками:
flex column 1:

- `Axiom Station`
- `Division of Behavioral Inference`
- `Sector: Kepler Relay 7`
- `Orbit: Vanta-3 Research Ring`

flex column 2:
- `Signal Channel: XR-17`
- `Transmission Node: ORBIT-12`
- `Comms: contact@xenologic-station.net`

---

## Каркас сторінки XenoLogic Terminal

Ця сторінка вже не "майже звичайний сайт", а повністю diegetic terminal interface.

### Загальна структура

- label / badge / png title: `XenoLogic Terminal`
- великий екран терміналу
- під екраном – кнопки взаємодії

### Перший екран терміналу

Замість прямого слова `difficulty` користувач бачить сценічний запит на вибір `clearance level`.

На екрані:
- короткий in-world prompt
- три кнопки рівнів допуску

Рівні:
- `Observer Clearance` - зелена
- `Analyst Clearance` - жовта
- `Containment Clearance` - червона

### Екрани сесії

Після вибору допуску користувач переходить у quiz flow.

Формат екрана:
- terminal header
- case id, наприклад `Research Case #nnnnn-nnn`
- згенерований польовий звіт / кейс
- логічна умова у стилі референса
- три варіанти відповіді, серед яких один правильний

### Тип подачі кейсу

Кейс має звучати як фрагмент дослідницького звіту.

Приблизний формат:
- спостереження зонду / станції
- згадка виду, локації або об'єкта
- короткий опис поведінки істоти, взаємодії з іншими істотами або з об'єктами
- далі логічне твердження і питання: що випливає з наявних даних

### Кнопки відповіді

Під терміналом розташовані три кнопки:

flex row зліва направо: 
- `1`
- `2`
- `3`

Ці кнопки відповідають трьом варіантам відповіді й дозволяють вибрати той distractor / висновок, який користувач вважає правильним.

### Візуальний принцип terminal flow

- homepage більш стандартна і сюжетна
- terminal pages повністю беруть на себе diegetic sci-fi UI
- саме terminal flow найближчий до Python-референса за структурою взаємодії

---

##  Відкриті питання

Ці питання ще не зафіксовані остаточно й мають бути узгоджені перед деталізацією homepage content:

- чи homepage більше `clean research`, чи більше `signal mystery`
- чи species block показує одну фокусну расу, чи кілька прикладів
- наскільки явно на головній сторінці показувати actual quiz interface
- який саме CTA буде головним
- як далеко в course implementation заходити в diegetic UI language

---

## Фази розробки

## Phase 1 – Oppgave 1 ✓ 

**Мета:**
- Створити задумку і концепцію для `XenoLogic`, яка буде реалізована в MVP
- Перенести з референса `LogikkQuiz` лише те, що потрібно для реалізації MVP, і адаптувати це до alien-only domain
- Визначити основні продуктові рамки, які будуть керувати дизайном і реалізацією MVP

## Phase 2 – Oppgave 2 ✓ 

**Мета:**
- Перекласти продуктний задум у чіткий Figma-напрям для `XenoLogic`
- Зафіксувати візуальний тон, layout principle, палітру, типографіку і базову UI-мову
- Побудувати wireframe і final design для desktop та mobile
- Визначити, як продукт має виглядати в межах реалістичної HTML/CSS-реалізації
- Підготувати homepage і terminal direction як візуальну основу для наступної кодової фази


## Phase 3 – Oppgave 3

**Мета:**
- Перенести вже прийнятий дизайн у реальний `HTML/CSS`-проєкт
- Побудувати перший публікабельний multipage-зріз `XenoLogic` у межах курсу
- Реалізувати кілька живих сторінок із реальною навігацією замість повного quiz engine
- Зберегти фокус на семантичному HTML, layout, responsive design, typography і чистому CSS
- Використати `JavaScript` лише там, де він справді потрібен, не перетворюючи вправу на JS-heavy реалізацію
- Використати легкий `JavaScript` для procedural `Station Feed`, щоб на homepage з'являлись випадкові in-world новини
- Підготувати базу для подальшого перенесення реальної логіки продукту в наступних фазах

**Робочий delivery slice:**
- `Homepage` – entry point, tone, CTA, station feed
- `Inference Protocols` – жива контентна сторінка на основі `Logic ops.md`
- `Xenopedia` – жива worldbuilding/content page з навігаційною цінністю (опціонально)


---


