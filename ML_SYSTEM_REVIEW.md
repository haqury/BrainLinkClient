# Обзор системы ML: обучение и предсказания

**Дата:** 2026-08-13  
**Статус:** только анализ, логику не меняем  
**Цель:** зафиксировать как сейчас устроено ML и что можно улучшить

---

## 1. Карта компонентов

| Компонент | Файл | Роль |
|-----------|------|------|
| Данные / конфиг | `models/ml_models.py` | `MLTrainingData`, `MLConfig`, `MLPrediction` |
| Обучение | `services/ml_trainer_service.py` | сбор сэмплов, auto-train, RF/SVM/MLP, save/load pickle |
| Предсказание | `services/ml_predictor_service.py` | features → scaler → model → probs → event |
| UI | `ui/ml_control_form.py` | сбор, train, threshold, feature weights, invert ml/mr |
| Интеграция | `ui/main_window.py` | режим Base/ML, SHM в игру, импорт из history, game config |
| Модель на диске | `models_ml/brainlink_classifier.pkl` | `{model, scaler}` |

Параллельный путь (не ML): rule-based history match в `services/history_service.py` (Base).

---

## 2. Как работает сейчас (as-is)

### 2.1 Признаки (features)

10 скаляров на один пакет EEG:

`attention, meditation, delta, theta, low_alpha, high_alpha, low_beta, high_beta, low_gamma, high_gamma`

- Нет `signal` (качество сигнала).
- Нет временного окна (дельты, rolling mean/std, последовательности).
- Каждый пакет = независимый сэмпл.
- `feature_weights` (по умолчанию attention/meditation = 0.2) умножаются **до** `StandardScaler`.

### 2.2 Сбор обучающих данных

Источники:

1. **Collect Training Data** + удержание стрелок / чекбоксов → каждый EEG-пакет с `label_event_name` идёт в `ml_trainer.add_training_sample`.
2. **Import from history** — записи с `event_name` из history.
3. Команды из игры (shared memory) могут добавлять сэмплы.

Защита от feedback loop: в train идут только ручные лейблы (`label_event_name`), не ML-предсказания.

Важно:

- При удержании клавиши пишется **много почти одинаковых** соседних пакетов → сильная автокорреляция.
- Отдельный JSON training dataset больше не персистится; данные в основном runtime + history.
- History при ML-режиме **не** пополняется автоматически (`add` только если ML выключен).

### 2.3 Обучение

- Модели: `RandomForest` (default), `SVM(RBF, probability=True)`, `MLP(100,50)`.
- RF/SVM: `class_weight='balanced'`; MLP — без class_weight.
- Split: `test_size=0.2`, stratify если у каждого класса ≥2 сэмпла; иначе fallback.
- Scaler: `StandardScaler` fit на train, сохраняется вместе с моделью.
- Обучение в **отдельном process** (Windows spawn), данные через temp JSON + result Queue.
- Auto-train: каждые `auto_train_min_new_samples` (по умолчанию 4) новых сэмпла, если `can_train()`.
- Пороги: `min_samples_per_class=4`, `min_classes_required=1` (можно учить на одном классе).

Метрики: train/test accuracy, classification_report, confusion_matrix, event_distribution.

### 2.4 Предсказание (runtime)

1. Features + `feature_weights`.
2. `scaler.transform` (если есть).
3. `predict` / `predict_proba`.
4. **Class weights** (из game config `prediction_weights`) умножают probs → argmax для класса.
5. **Confidence** = max(**сырых** probabilities), не взвешенных.
6. Threshold (`confidence_threshold`, default 0.6) — влияет на UI/логирование; в игру low-conf event всё равно уходит для scaling скорости.
7. Опционально `invert_ml_mr`.
8. При включённом ML **нет fallback на Base** — при ошибке/не готовности шлётся пустой event.

### 2.5 Связь с игрой

Shared memory: `event`, `ml_confidence`, `ml_probabilities`.  
Game config (`--game-config`): threshold, model_path, prediction_weights.  
Команда Type 3: сохранить модель по пути из game config.

---

## 3. Сильные стороны (что уже хорошо)

- Разделение лейбла и предсказания (нет самообучения на своих выходах).
- Обучение вне UI-потока (multiprocess).
- Scaler + сохранение в одном pickle.
- Баланс классов в RF/SVM.
- Настраиваемые feature/class weights и threshold из UI/игры.
- Явный переключатель Base / ML.
- Импорт из history как способ переиспользовать ручную разметку.

---

## 4. Проблемы и риски (найденные при разборе)

### P1. Высокий приоритет

| # | Проблема | Почему важно |
|---|----------|--------------|
| P1.1 | **`feature_weights` не передаются в process-training** (`config_dict` в `start_auto_training` без `feature_weights`) | UI меняет веса, а auto/manual process train учит на defaults dataclass. Sync-train веса видит, process — нет. Поведение расходится. |
| P1.2 | **Сильно коррелированные сэмплы при удержании клавиши** | Test accuracy завышена: соседние пакеты попадают и в train, и в test. Модель «запоминает момент», а не состояние. |
| P1.3 | **Confidence vs class_weights рассинхрон** | Класс выбирается по weighted probs, confidence — по raw max. Игра может крутить скорость «уверенностью», которая не соответствует выбранному классу. |
| P1.4 | **Нет учёта качества сигнала** | Плохой контакт → мусорные features → мусорные лейблы и предсказания. |

### P2. Средний приоритет

| # | Проблема | Почему важно |
|---|----------|--------------|
| P2.1 | Только snapshot features, нет динамики | Мысленные команды — процесс во времени; один кадр слабее окна 0.5–2 с. |
| P2.2 | `min_classes_required=1` | Модель всегда предсказывает единственный класс; «accuracy» бессмысленна. |
| P2.3 | Validation при `load_model` без scaler / weights | Dummy predict может пройти или упасть некорректно; слабая проверка совместимости. |
| P2.4 | MLP без `class_weight` / early stopping | Хуже на дисбалансе; дольше и нестабильнее. |
| P2.5 | Auto-retrain каждые 4 сэмпла | Частое полное переобучение RF на всём датасете; шум модели «плавает» во время сессии. |
| P2.6 | Training data не персистится отдельно | После рестарта буфер trainer пуст, пока не import history / новый collect. Модель на диске есть, датасет в RAM — нет. |
| P2.7 | History не пишется в ML-режиме | Сложнее копить размеченные данные «во время игры на ML». |

### P3. Низкий / UX / инфраструктура

| # | Проблема |
|---|----------|
| P3.1 | Метрики только accuracy; нет per-class F1 в UI как главного индикатора, нет калибровки probs |
| P3.2 | Нет версионирования модели (какие feature_weights / sklearn version внутри pkl) |
| P3.3 | `invert_ml_mr` — костыль вместо разбора причины инверсии |
| P3.4 | Sticky debounce событий есть для Base/SHM, но ML flicker может жить на уровне probs |
| P3.5 | README (`ML_MODULE_README.md`) частично устарел (отдельный training_data JSON и т.п.) |

---

## 5. Идеи улучшений (предложения, без реализации)

Сгруппированы от «быстрого фикса» к «архитектурным».

### A. Быстрые фиксы (малый риск)

1. **Передавать полный config в process**  
   В `config_dict` добавить: `feature_weights`, `min_classes_required`, и всё остальное из `MLConfig`, что влияет на train.

2. **Confidence согласовать с выбором класса**  
   Варианты:  
   - confidence = weighted_prob[chosen] / sum(weighted); или  
   - сначала выбрать класс по raw, weights только как bias в UI;  
   - явно логировать оба значения.

3. **Фильтр по signal**  
   Не писать в train и не предсказывать (или confidence↓), если signal выше порога «плохо» (зависит от шкалы устройства).

4. **Поднять `min_classes_required` до 2** (или не давать Enable ML при 1 классе).

5. **Дедуп / прореживание при collect**  
   Писать не каждый пакет, а 1 из N, или только если features сменились на ε, или раз в 200–500 ms.

### B. Качество данных и оценки

6. **Group / time-aware split**  
   Резать train/test по времени или по «сессиям удержания клавиши», а не случайно по пакетам.

7. **Баланс и квоты классов**  
   Показывать «мало md / много stop»; опционально downsample majority.

8. **Калибровка вероятностей**  
   `CalibratedClassifierCV` или temperature scaling — чтобы threshold 0.6 был осмысленнее для игры.

9. **Персист training buffer**  
   Опционально сохранять `ml_training_buffer.json` рядом с моделью (или восстанавливать из history при старте автоматически).

### C. Лучшие признаки / модель

10. **Временное окно**  
    Накопленный буфер 1–2 с: mean/std/slope по каждой полосе + attention/meditation.  
    Это самый сильный ожидаемый прирост качества для EEG-команд.

11. **Относительные признаки**  
    Например `beta/alpha`, `theta/beta`, лог-спектры — меньше зависимость от абсолютного масштаба устройства.

12. **Модель по умолчанию**  
    Оставить RF, но:  
    - `class_weight='balanced_subsample'`;  
    - ограничить глубину / min_samples_leaf против оверфита на дубликатах;  
    - опционально `HistGradientBoosting` / легкий GBDT.

13. **Online / incremental**  
    Вместо полного retrain каждые 4 сэмпла — копить N (например 20–50) или retrain по кнопке / таймеру.

### D. Runtime / UX предсказаний

14. **Сглаживание предсказаний**  
    Majority vote / EMA по последним K пакетам (аналог sticky для Base). Снизит дрожание ml↔mr.

15. **Гибрид Base + ML**  
    Опционально: если ML low-conf — мягкий fallback на history match (сейчас жёстко запрещено).  
    Нужно продуманно, чтобы не вернуть старые баги «ML включён, а едет Base».

16. **Раздельные пороги**  
    `emit_threshold` (когда вообще слать event) vs `full_speed_threshold` (игра уже частично так думает через confidence).

17. **Диагностика в UI**  
    Live: probs bar, chosen class, signal, «почему пусто» (not ready / low conf / bad signal).

### E. Интеграция и эксплуатация

18. **Метаданные в pkl**  
    `{model, scaler, feature_names, feature_weights, trained_at, n_samples, sklearn_version, class_labels}`.

19. **Авто-import history при старте** (опционально, с флагом) — чтобы auto-train и статистика не были «пустыми» после рестарта.

20. **A/B сессии**  
    Лог: timestamp, features hash, pred, conf, label (если был) — для офлайн-анализа ошибок.

---

## 6. Приоритетный roadmap (предложение)

| Этап | Что сделать | Ожидаемый эффект |
|------|-------------|------------------|
| **0. Correctness** | P1.1 feature_weights в process; P1.3 confidence vs weights | Предсказуемое обучение/скорость в игре |
| **1. Data hygiene** | прореживание collect; filter signal; min 2 classes | Меньше мусора, честнее метрики |
| **2. Temporal features** | окно mean/std/slope | Главный прирост качества команд |
| **3. Stability** | сглаживание pred + реже retrain | Меньше дрожи в игре |
| **4. Eval** | time-based split + F1 per class в UI | Понятно, улучшаемся ли реально |

---

## 7. Открытые вопросы (нужно решить до правок)

1. **Собирать train во время ML-режима?** Сейчас history не пишется при ML — это сознательно или ограничение?
2. **Нужен ли гибрид Base↔ML** при low confidence, или игра должна сама решать только по `ml_confidence`?
3. **Какая целевая латентность?** Окно 2 с улучшает качество, но добавляет задержку.
4. **Сколько классов реально нужно в проде?** (часто только ml/mr vs все 5)
5. **Кто source of truth для feature_weights** — UI клиента или game config?

---

## 8. Краткие выводы

Система уже рабочая end-to-end: collect → train (background) → predict → SHM/game.  
Главные рычаги улучшения сейчас не «новая нейросеть», а:

1. **честные данные** (меньше дубликатов, signal gate, правильный split);  
2. **фиксы consistency** (weights в process train, confidence);  
3. **время в признаках** (окно, не один пакет);  
4. **стабилизация выхода** (сглаживание + реже retrain).

Код в этом шаге **не менялся** — только зафиксировали картину и идеи.
