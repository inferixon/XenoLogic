# LogikkQuiz — Logisk Tenkning

> Тренажер логічного мислення з динамічно згенерованими задачами в стилі тесту Войнаровського.

## Що це

LogikkQuiz — інтерактивний тренажер логіки для дітей. Дитина читає твердження (сценарій), аналізує логічні зв'язки і обирає правильний висновок з 3 варіантів. Сценарії генеруються динамічно з комбінації entities + properties (template-based), що дає 36,000+ унікальних питань.

## Для кого

Дитина 7–12 років. Тренує:
- Логічне мислення (імплікація, дедукція)
- Критичне читання (що саме сказано vs що здається)
- Розпізнавання хибних висновків (fallacies)

## Як працює

### Потік гри (ідентичний MatteQuiz)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INTRO     │ ──► │    GAME     │ ──► │   RESULTS   │
│             │     │             │     │ (intro mode)│
└─────────────┘     └─────────────┘     └─────────────┘
     │                                        │
     └────────────────────────────────────────┘
                    (same screen)
```

1. **Інтро** → Title, subtitle, play button (центр)
2. **Гра** → N питань, 3 варіанти кожне
3. **Результат** → Icons row (stars) + bonus, saveclose button (на launcher screen)

### Формат питання

```
┌────────────────────────────────────────────────────────────┐
│                     Oppgave 3 av 10                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  "Alle katter liker melk.                            │  │
│  │   Milo er en katt.                                   │  │
│  │   Hva kan vi si om Milo?"                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│           ┌──────────────────────────┐                     │
│           │    Milo liker melk.      │  ← correct          │
│           └──────────────────────────┘                     │
│           ┌──────────────────────────┐                     │
│           │    Milo er en hund.      │  ← distractor       │
│           └──────────────────────────┘                     │
│           ┌──────────────────────────┐                     │
│           │    Vi vet ikke.          │  ← distractor       │
│           └──────────────────────────┘                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## UI Structure (копія MatteQuiz)

### MatteQuizWidget → LogikkQuizWidget

**Наслідуємо**: `BaseQuizWidget`

**Ідентичні елементи:**
- `intro_widget` — title block, intro label, play button, icons container, saveclose
- `game_widget` — progress label, question label (statement), answer buttons
- `service_buttons_toolbar` — dashboard/settings/home (intro), back/home (game)
- `status_bar` — utilons display

### Intro Screen
```python
# Title block (header)
self.intro_title_block  # "LOGIKKQUIZ" + subtitle

# Intro label
self.intro_label  # "Du skal svare på {N} spørsmål"

# Icons container (for results)
self.icons_container  # Stars display after quiz

# Play button (центр)
self.start_button = PlayButton(self.start_game, UI_CONFIG)

# SaveClose button (hidden until results)
self.saveclose_button = SaveCloseButton(...)
```

### Game Screen
```python
# Progress indicator
self.progress_label  # "Oppgave 3 av 10"

# Question container (2/3 width, centered)
self.question_label  # Statement text (white bg, border, rounded)

# Answer buttons (1/4 width, centered, VERTICAL)
self.answer_buttons = []  # 3 buttons (vs 4 in MatteQuiz)
for i in range(3):
    btn = QPushButton()
    btn.clicked.connect(lambda checked, idx=i: self.answer_selected(idx))
```

### Service Buttons (як MatteQuiz)
```python
# Intro mode: dashboard, settings, home
# Game mode: back, home
# Settings mode: back
```

---

## Категорії логічних операцій (27 типів)

| Категорія | Операції |
|-----------|----------|
| Імплікація | modus_ponens, modus_tollens, hypothetical_syllogism, contraposition |
| Заперечення | double_negation, negation_introduction, de_morgan |
| Квантори | universal_instantiation, existential_instantiation, quantifier_all, quantifier_none |
| Зв'язки | conjunction, disjunction_incl, disjunction_excl, disjunctive_syllogism |
| Класи | class_membership, subclass, exception |
| Металогіка | insufficient_info, contradiction, excluded_middle, incompatibility |
| Темпоральні | temporal_always, temporal_sometimes |
| Пастки | affirming_consequent_trap, denying_antecedent_trap |
| Модальна логіка | possibility_implication |

### Рівні складності (1–3)

**Ключовий принцип:** Складність визначається **якістю дистракторів**, а не типом логічної операції. Всі типи операцій доступні на всіх рівнях.

#### Рівень 1 — Навчальний

**Операції:** Всі, крім `insufficient_info` та комплексних ланцюгів (>2 кроки)

**Дистрактори:**
- Очевидно неправильні, але НЕ примітивні
- Порушують логіку умови, але мають зв'язок з контекстом
- ❌ Заборонено: `class_swap` типу "Milo er en hund" (занадто тупо)
- ✅ Дозволено: `denying_antecedent`, `false_uncertain`, м'який `quantifier_shift`

**Приклад:**
```
Hvis det regner, blir bakken våt.
Det regner.
→ Hva kan vi si om bakken?

✓ Bakken er våt.
✗ Det er ikke sikkert. (false_uncertain - м'який)
✗ Bakken blir våt bare noen ganger. (quantifier_shift)
```

#### Рівень 2 — Стандартний (≈ тест Войнаровського)

**Операції:** Всі, включаючи `insufficient_info`

**Дистрактори:**
- Середньої складності, потребують уважного читання
- Логічні помилки замасковані правдоподібністю
- Можуть включати `affirming_consequent`, `predicate_swap`

**⚠️ Prior Knowledge Problem:**
Для операцій типу `insufficient_info` реальні об'єкти (пінгвіни, коти) створюють конфлікт — дитина знає відповідь з біології, а не з логіки.

**Рішення: 6 категорій фантастичних істот**

| Категорія | Приклади | Кількість |
|-----------|----------|-----------|
| folkevesen | hulder, troll, nisse, nøkken, draugen, vetter, fossegrim... | 18 |
| romvesen | glorp, blimp, zaxer, flim, trax, mork, plunk... | 15 |
| fabeldyr | fenristass, mjødnøff, skyggeulv, nordlyskatt... | 12 |
| havuhyre | fjordsnegle, tangtroll, sjøtusse, plaskekraken... | 10 |
| mutantdyr | trollhund, nissekatt, runeku, pannekakeand... | 12 |
| godtevesen | lakrisnisse, gelétroll, sjokosnute, marsipanmår... | 10 |

**+ Mutant Generator** для динамічних істот:
- Prefixes: rune-, troll-, skygge-, snø-, måne-...
- Suffixes: -tass, -snute, -klump, -bølle...
- Base animals: katt, mus, elefant, kenguru...

**Чому працює:** Фантастичні істоти → дитина знає що це вигадка → чиста логіка!у

**Приклад (folkevesen):**
```
En hulder fniser i busken.
Alle som fniser i busken, danser på taksteinene.
→ Hva kan vi si om hulderen?

✓ Hulderen danser på taksteinene.
✗ Vi vet ikke. (false_uncertain)
✗ Hulderen fniser noen ganger. (quantifier_shift)
```

**Приклад (romvesen):**
```
En glorp svever i stua.
Alle som svever i stua, blunker i kjøleskapet.
→ Hva kan vi si om glorpen?

✓ Glorpen blunker i kjøleskapet.
✗ Glorpen er en blimp. (class_swap)
✗ Vi vet ikke om glorpen blunker. (false_uncertain)
```

**Чому працює:** Веселі безглузді дії → дитина не може "здогадатись" → чиста логіка!

#### Рівень 3 — Експертний

**Операції:** Всі + комплексні ланцюги (3+ кроки), контрапозиція, де Морган

**Дистрактори:**
- Тонкі маніпуляції, жодних очевидних фолсів
- Всі варіанти виглядають правдоподібно
- Вимагають точного аналізу кожного слова
- Використовують: `subtle_quantifier_shift`, `scope_ambiguity`, `temporal_confusion`

**Приклад:**
```
Alle som trener regelmessig, blir sterkere.
Noen som blir sterkere, spiser sunt.
→ Hva kan vi si om de som trener regelmessig?

✓ Noen av dem spiser kanskje sunt. (correct - "kanskje" важливе!)
✗ Alle som trener, spiser sunt. (quantifier_shift: noen→alle)
✗ De blir sterkere og spiser sunt. (conjunction_fallacy)
```

### Матриця дистракторів за рівнями

| Distractor Type | Рівень 1 | Рівень 2 | Рівень 3 |
|-----------------|:--------:|:--------:|:--------:|
| `class_swap` (тупий) | ❌ | ❌ | ❌ |
| `false_uncertain` | ✅ | ✅ | ⚠️ subtle |
| `denying_antecedent` | ✅ | ✅ | ✅ |
| `affirming_consequent` | ⚠️ obvious | ✅ | ✅ |
| `quantifier_shift` | ⚠️ obvious | ✅ | ✅ subtle |
| `predicate_swap` | ❌ | ✅ | ✅ |
| `chain_break` | ❌ | ✅ | ✅ |
| `scope_ambiguity` | ❌ | ❌ | ✅ |
| `temporal_confusion` | ❌ | ⚠️ | ✅ |
| `conjunction_fallacy` | ❌ | ✅ | ✅ |

---

## Генерація питань

### QuestionGenerator (як MatteQuiz)

```python
class LogicQuestionGenerator:
    def __init__(self, config: dict, difficulty: int = 1):
        self.config = config
        self.difficulty = difficulty
        self.operation_types = config.get("operation_types", [])
    
    def generate_modus_ponens(self, op_type: dict) -> dict:
        """Generate modus ponens question"""
        template = random.choice(op_type["templates"])
        # Fill template with theme-specific content
        return {
            "statement": template["statement"],
            "question": template["question"],
            "options": shuffle([correct, distractor1, distractor2]),
            "correct": 0,  # index after shuffle
            "type": "modus_ponens"
        }
```

### MVP: Template-based Generation (Phase 1-3)

Комбінаторика шаблонів дає **36,000+ унікальних питань** — достатньо на роки без повторів.

**Структура в `app_logikkquiz.json`:**
```json
{
  "entities": {
    "folkevesen": ["hulder", "troll", "nisse", "nøkken", ...18 total],
    "romvesen": ["glorp", "blimp", "zaxer", "flim", ...15 total],
    "fabeldyr": ["fenristass", "mjødnøff", "skyggeulv", ...12 total],
    "havuhyre": ["fjordsnegle", "tangtroll", "sjøtusse", ...10 total],
    "mutantdyr": ["trollhund", "nissekatt", "runeku", ...12 total],
    "godtevesen": ["lakrisnisse", "gelétroll", "sjokosnute", ...10 total]
  },
  "properties": {
    "folkevesen": ["fniser i busken", "hvisker i postkassa", "danser på taksteinene", ...16 total],
    "romvesen": ["svever i stua", "snurrer i trillebåra", "blunker i kjøleskapet", ...16 total],
    "fabeldyr": ["brøler i pannekakerøra", "gløder i ryggsekken", ...16 total],
    "havuhyre": ["plasker i vanndammen", "bobler i badekaret", ...16 total],
    "mutantdyr": ["mjauer i rustninga", "bjeffer i blomsterpotta", ...16 total],
    "godtevesen": ["slurper i kakaoen", "smatter på vaffelen", ...16 total]
  },
  "mutant_generator": {
    "prefixes": ["rune", "troll", "skygge", ...11 total],
    "suffixes": ["tass", "snute", "klump", ...10 total],
    "base_animals": ["katt", "mus", "elefant", ...15 total]
  }
}
```

**Комбінаторика:**
- 6 категорій × 10-18 сутностей × 16 властивостей × 27 операцій × 3 рівні = **100,000+**

### Phase 4 (Optional): Cometa/GPT Enhancement

Якщо шаблонів буде недостатньо — додати GPT генерацію з кешуванням:
- GPT генерує нові питання
- Кешуються в `app_logikkquiz_qdb.json`
- Формат ідентичний шаблонному

---

## Дистрактори (повний каталог)

### Базові (рівні 1-3)
| ID | Назва | Опис | Приклад |
|----|-------|------|---------|
| `affirming_consequent` | B ⊢ A | Зворотна імплікація | "Bakken er våt → det regner" |
| `denying_antecedent` | ¬A ⊢ ¬B | Заперечення антецедента | "Det regner ikke → bakken er tørr" |
| `quantifier_shift` | alle↔noen↔ingen | Зсув квантора | "Noen fugler" → "Alle fugler" |
| `false_uncertain` | "Vi vet ikke" | Хибна невизначеність | Коли насправді можна визначити |

### Середні (рівні 2-3)
| ID | Назва | Опис | Приклад |
|----|-------|------|---------|
| `predicate_swap` | Підміна властивості | Властивість не з умови | "har fjær" → "kan fly" |
| `chain_break` | Обрив ланцюга | A→B, B→C ⊢ тільки B | Ігнорування транзитивності |
| `conjunction_fallacy` | A ∧ B замість A | Додавання зайвої умови | "sterkere OG spiser sunt" |
| `temporal_confusion` | Плутанина часу | alltid↔noen ganger | "завжди" → "іноді" |

### Експертні (рівень 3)
| ID | Назва | Опис | Приклад |
|----|-------|------|---------|
| `scope_ambiguity` | Неоднозначність scope | Квантор до чого відноситься | "Alle som... noen av dem..." |
| `subtle_quantifier` | Тонкий зсув квантора | kanskje, sannsynligvis | "spiser" → "spiser kanskje" |
| `modality_shift` | Зсув модальності | може↔мусить | "kan" → "må" |
| `negation_scope` | Scope заперечення | ¬(A∧B) vs (¬A)∧B | Де саме "ikke" |

### Заборонені (занадто примітивні)
| ID | Причина заборони |
|----|------------------|
| `class_swap` (тупий) | "Milo er en katt" → "Milo er en hund" — очевидно абсурдно |
| `random_statement` | Твердження без зв'язку з умовою |
| `emotional_appeal` | Чисто емоційний варіант без логіки |

---

## Утілони

**Формула:** 1 утілон за правильну відповідь (як MatteQuiz)

**Bonus:** +2 утілони за 100% правильних у сесії

---

## Файлова структура

```
src/
├── apps/
│   └── logikkquiz/
│       ├── __init__.py
│       └── logikkquiz.py          # LogikkQuizWidget (3043 рядки)
├── config/
│   └── app_logikkquiz.json        # Entities, properties, operation_types, UI (445 рядків)
assets/
└── icons/
    └── app_logikkquiz.png         # Іконка модуля
```

*Note: `cache/logikkquiz/` та `app_logikkquiz_qdb.json` не існують — генерація повністю template-based.*

---

## Конфігурація (app_logikkquiz.json)

**Структура ідентична `app_mattequiz.json`** — ті ж ключі, ті ж значення UI.

```json
{
  "game": {
    "total_questions": 10,
    "difficulty_level": 1,
    "answer_count": 3,
    "settings_ranges": {
      "questions_min": 5,
      "questions_max": 30,
      "difficulty_min": 1,
      "difficulty_max": 3
    }
  },
  "ui": {
    "background_color": "#D8DFE5",
    "text_color": "#2C3E50",
    "border_color": "#6C757D",
    "accent_color": "#007FFF",
    "hover_color": "#b3cfff",
    "button_color": "#E9ECEF",
    "correct_color": "#ccffcc",
    "error_color": "#ffcccc"
  },
  "fonts": {
    "main": "Palatino Linotype",
    "intro_size": 42,
    "question_size": 28,
    "answer_size": 24,
    "progress_size": 36,
    "result_size": 32,
    "settings_title_size": 42,
    "settings_label_size": 34
  },
  "texts": {
    "title": "LOGIKKQUIZ",
    "intro_title": "LOGIKKQUIZ",
    "intro_subtitle": "Logisk tenkning",
    "intro": "Du skal svare på {questions} logikkoppgaver.\nLes nøye og tenk logisk!",
    "start_button": "⭐️ START",
    "progress_template": "Oppgave {current}/{total}",
    "result_template": "Resultat: {score}/{total}\n\n{stars}",
    "settings_title": "INNSTILLINGER"
  },
  "operation_types": [
    {
      "id": "modus_ponens",
      "name": "Modus Ponens",
      "category": "implication",
      "templates": [
        {
          "statement": "Hvis det regner, blir bakken våt.\nDet regner.",
          "question": "Hva kan vi si om bakken?",
          "correct": "Bakken er våt.",
          "distractors": {
            "1": [
              {"text": "Det er ikke sikkert.", "fallacy": "false_uncertain"},
              {"text": "Bakken blir våt bare noen ganger.", "fallacy": "quantifier_shift"}
            ],
            "2": [
              {"text": "Bakken er tørr.", "fallacy": "denying_antecedent"},
              {"text": "Vi kan ikke vite det.", "fallacy": "false_uncertain"}
            ],
            "3": [
              {"text": "Bakken kan være våt.", "fallacy": "modality_shift"},
              {"text": "Det avhenger av været.", "fallacy": "scope_ambiguity"}
            ]
          }
        }
      ]
    }
  ],
  "themes": ["dyr", "mat", "vær", "leker", "skole", "sport", "folkevesen", "romvesen"]
}
```

**Відмінності від MatteQuiz:**
- `answer_count`: 3 (замість 4)
- `question_size`: 28 (менше, бо довший текст)
- `operation_types` замість `question_types`
- Дистрактори розбиті за рівнями складності (1/2/3)

---

## Реалізація

### Phase 1: Core Structure ✅
- [x] Створити `src/apps/logikkquiz/logikkquiz.py` (3043 рядки)
- [x] Скопіювати структуру з MatteQuiz (intro/game/results flow)
- [x] Змінити 4 кнопки → 3 кнопки
- [x] Створити `app_logikkquiz.json` (445 рядків)
- [x] Інтегрувати в launcher (`launch_logikkquiz()`)
- [x] Іконка: `assets/icons/app_logikkquiz.png`

### Phase 2: Question Generator ✅
- [x] `LogicQuestionGenerator` class
- [x] **27 типів операцій** (більше ніж планувалось!)
- [x] 6 категорій entities (folkevesen, romvesen, fabeldyr, havuhyre, mutantdyr, godtevesen)
- [x] Mutant generator для динамічних істот
- [x] Distractor selection logic за рівнями складності

### Phase 3: UI Polish ✅
- [x] Statement widget styling (multiline support)
- [x] Correct/incorrect feedback (green/red як MatteQuiz)
- [x] Icons row (stars) on results
- [x] Stats integration (`stats.json`)

### Phase 4: Cometa Integration ⬜ (optional)
- [ ] GPT prompt design
- [ ] `app_logikkquiz_qdb.json` cache
- [ ] Fallback to templates
- *Note: Template-based генерація дає 36,000+ питань — GPT не потрібен*

### Phase 5: Advanced ✅
- [x] Рівень 3 templates (всі 3 рівні реалізовано)
- [x] Dashboard panel (`LogikkQuizStatsModal` + `AccuracyChartWidget`)
- [ ] TTS (optional, не потрібно)

---

## Ключові відмінності від MatteQuiz

| Аспект | MatteQuiz | LogikkQuiz |
|--------|-----------|------------|
| `answer_count` | 4 | **3** |
| Тип контенту | Математичні вирази | Текстові сценарії |
| Генератор | `question_types` + формули | **27 operation_types** + dynamic entities |
| Question label | Короткий текст | **Multiline statement** |
| Дистрактори | Числові (nearby) | За fallacy type + рівень |
| Entities | — | 6 категорій (folkevesen, romvesen, fabeldyr...) |
| Mutant generator | — | Динамічні істоти (prefix+suffix+base) |
| Іконка | `app_mattequiz.png` | `app_logikkquiz.png` |

**Все інше ідентичне:**
- UI colors, fonts, sizes — копія
- Intro/Game/Results flow — копія
- Service buttons — копія
- Settings overlay — копія
- Stats integration — копія
- StatusBar — копія

---

## Референси

- **`src/apps/mattequiz/mattequiz.py`** — UI structure, BaseQuizWidget usage
- **`src/config/app_mattequiz.json`** — config format
- **Тест Войнаровського** — logic puzzle format

---

*Статус: ✅ Completed (січень 2026)*
*Phase 1-3, 5 — Done. Phase 4 (GPT) — optional, не потрібен.*
