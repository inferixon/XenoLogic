 # XenoLogic — DevPlan Full Product UA

Full Product є наступним розширенням після MVP.

### У Full Product можуть увійти

- багато класів alien species
- окремі поведінкові патерни для кожної раси
- ширший lore
- модулі, місії, архівні кейси
- додаткові типи подачі матеріалу
- аудіо / відео / signal logs
- складніший UI
- багатомовність
- розширені presentation layers
- AI generation for station news feed
- session persistence і resume flow

### Можливе розширення terminal navigation у Full Product

У Full Product terminal може перейти від простого session-lock flow до повноцінного persistent navigation model.

Ідея:
- активна session зберігає свій стан
- користувач може тимчасово вийти з quiz flow
- при поверненні система пропонує `Resume session`
- це може працювати навіть якщо користувач випадково повернувся на homepage

Що саме може зберігатися:
- вибраний `clearance level`
- номер поточного питання
- already answered cases
- score / accuracy snapshot
- session timestamp

Можливі сценарії:
- користувач вийшов у `Homepage` і бачить кнопку `Resume active session`
- користувач відкрив `Xenopedia` або `Inference Protocols` як довідку, а потім повернувся до terminal
- система може попереджати, що старт нової сесії обнулить попередню

Технічно це вже не є обов'язковою частиною MVP, але є природним напрямом еволюції продукту після базового terminal flow.

### Потенційні species groups

- `Aetherids`
- `Gravorms`
- `Mirex`
- `Noxians`
- `Cryolings`
- `Voidborn`
- `Hive Minds`
- `Gas Beings`
- `Parasite Intelligences`