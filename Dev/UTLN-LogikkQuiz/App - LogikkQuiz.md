# LogikkQuiz — Logikktrening

> Логічний квіз на основі тесту Войнаровського: 27 типів логічних операцій.

## Що це

LogikkQuiz — тренажер формальної логіки. Дитина отримує логічну задачу з двома посилками та обирає правильний висновок з 3 варіантів. Всі задачі генеруються динамічно з норвезьким фольклорним контекстом (тролі, ніссе, космічні істоти).

## Для кого

Дитина 7–12 років. Тренує формальне мислення, розпізнавання логічних помилок, критичний аналіз аргументів.

## Як працює

### Потік гри

1. **Інтро** → Показує кількість питань, рівень складності
2. **Гра** → 10 питань, 3 варіанти відповіді кожне
3. **Результат** → Точність + утілони + статистика

### Типи операцій (27)

| Категорія | Операції |
|-----------|----------|
| Базова логіка | modus_ponens, modus_tollens, contraposition |
| Силогізми | disjunctive_syllogism, hypothetical_syllogism |
| Квантори | universal_instantiation, existential_instantiation, quantifier_all, quantifier_none |
| Заперечення | negation_introduction, double_negation |
| Кон'юнкція/Диз'юнкція | conjunction, disjunction_incl, disjunction_excl |
| Теорія множин | class_membership, subclass |
| Темпоральна логіка | temporal_always, temporal_sometimes |
| Спеціальні | exception, incompatibility, insufficient_info |
| Закони логіки | contradiction, excluded_middle, de_morgan |
| Пастки | affirming_consequent_trap, denying_antecedent_trap |
| Модальна логіка | possibility_implication |

### Приклад задачі (Modus Ponens)

> **Посилка 1:** Hvis en soppnisse fniser i busken, så bobler den i gryta.
> **Посилка 2:** En soppnisse fniser i busken.
> 
> **Hva følger logisk av dette?**
> - ✅ Soppnissen bobler i gryta
> - ❌ Soppnissen bobler ikke i gryta
> - ❌ Vi vet ikke om soppnissen bobler i gryta

Питання варіюються: кожен генератор має 3–4 формулювання (напр. "Hva kan vi konkludere?", "Hva følger logisk av dette?", "Hva må stemme da?").

### Генерація сутностей

Система динамічно комбінує:

| Тип | Приклади |
|-----|----------|
| Folkevesen | soppnisse, troll, nisse, bekkefant, mosegubbe, fossegrim |
| Romvesen | glorp, blimp, zaxer, flim, trax, mork |
| Fabeldyr | runetass, mjødnøff, tåkerev, nordlyskatt, snøfugl |
| Havuhyre | fjordsnegle, tangnisse, sjøtusse, boblefisk |
| Mutantdyr | fjellhund, nissekatt, runeku, glittersau |
| Godtevesen | lakrisnisse, gelévenn, sjokosnute, sukkervenn |

Та властивості:
> "fniser i busken", "hvisker i postkassa", "danser på taksteinene", "bobler i gryta"

### Мутант-генератор

15% шанс згенерувати унікальне ім'я замість статичної сутності:
- **Prefixes** (11): rune, troll, skygge, snø, måne, tåke, fjell, boble, hule, gelé, sjoko
- **Suffixes** (10): tass, snute, klump, bølle, fjomp, sprett, tut, plask, krabat, imp
- **Base words** (23): katt, mus, elefant, kenguru, pingvin, frosk, banan, gulrot, potet…

Приклади: "trollkatt", "snøbanan", "elefanttass", "gelépingvin"

~483 додаткових унікальних комбінацій.

### Рівні складності (1–3)

- **Level 1**: Прості дистрактори (очевидно неправильні)
- **Level 2**: Складніші дистрактори (часткові правди)
- **Level 3**: Тонкі логічні помилки як дистрактори

### Статистика

| Метрика | Опис |
|---------|------|
| Totalt økter | Всього сесій |
| Totalt oppgaver | Всього питань |
| Riktige svar | Правильних відповідей |
| Nøyaktighet | Точність (%) |
| STPO Beste/Siste/Snitt | Секунди на питання |
| Svake områder | Типи з найнижчою точністю (bullet-list, top 3) |

### Графік точності

Показує точність (%) або середній час (STPO) по днях.

### Утілони

**Формула:** 1 утілон за кожну правильну відповідь.
**Бонус:** +2 утілони за 100% точність (Flawless).

## Налаштування

В Settings можна змінити:
- Кількість питань (5–20)
- Рівень складності (1–3)

## Файли

| Файл | Призначення |
|------|-------------|
| `src/apps/logikkquiz/logikkquiz.py` | Основний модуль + LogicQuestionGenerator |
| `src/config/app_logikkquiz.json` | Типи операцій + сутності + UI |
| `src/config/stats.json` | Статистика (daily + aggregated) |

## Utility Functions

Функції в `logikkquiz.py` для коректної норвезької граматики:

| Функція | Призначення | Приклад |
|---------|-------------|---------|
| `negate_verb_phrase(phrase)` | Заперечення в **головному** реченні (V2) | `"svever i stua"` → `"svever ikke i stua"` |
| `negate_leddsetning(phrase)` | Заперечення в **підрядному** реченні (після at, hvis, som) | `"svever i stua"` → `"ikke svever i stua"` |
| `pluralize_category(category)` | Множина для категорій (з Noen/Alle/Ingen) | `"romvesen"` → `"romvesener"`, `"fabeldyr"` → `"fabeldyr"` |
| `to_infinitiv(phrase)` | Презенс → інфінітив | `"danser i kanelen"` → `"danse i kanelen"` |
| `shuffle_list(items)` | Перемішування варіантів відповідей | — |

### Граматичні правила

**Рід категорій (всі intetkjønn):**
- `"er et romvesen"` ✅ (не "en romvesen")
- `"er et folkevesen"` ✅

**Множина з кванторами:**
- `"Noen romvesener"` ✅ (не "Noen romvesen")
- `"Alle fabeldyr"` ✅ (-dyr незмінна)
- `"Ingen havuhyrer"` ✅

**Порядок слів у заперечення:**
- Головне речення: `"Glorp svever ikke i stua"` (ikke після дієслова)
- Підрядне (після at/hvis): `"at glorp ikke svever i stua"` (ikke перед дієсловом)

---

*Статус: ✅ Повністю імплементовано (лютий 2026)*
*Зроблено: 27 типів логічних операцій, динамічна генерація з фольклорним контекстом, варіації питань (3–4 на генератор), мутант-генератор, barnespråk-safe сутності, статистика з графіком*
