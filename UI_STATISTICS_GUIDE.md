# 📊 Где отображаются статистики в BrainLink Client

## 📋 Обзор

В BrainLink Client есть два места, где отображаются важные статистики:

1. **Главное окно** - количество записей в истории
2. **ML Control Form** - статистика ML обучения

---

## 1️⃣ История записей (Главное окно)

### Где находится:

**Раздел:** "History Management"  
**Расположение:** Главное окно BrainLink Client (нижняя часть)

### Что отображается:

```
History Management
├── File Path: [путь к файлу]
├── [Save to File] [Load from File] [Clear]
└── Records: 123  ← Количество записей в истории
```

### Как обновляется:

- Автоматически при добавлении новых записей
- При загрузке истории из файла
- При очистке истории

### Код:

- **Метка:** `self.lbl_counter` (строка 317 в `main_window.py`)
- **Метод обновления:** `update_counter()` (строка 829-831)
- **Источник данных:** `self.history_service.count()`

---

## 2️⃣ ML Training Statistics (ML Control Form)

### Где находится:

**Окно:** ML Control Form  
**Открыть:** Кнопка "ML Control" в главном окне

### Что отображается:

```
Status
├── Model: ✓ Trained and ready
├── Training samples: 45 (ml: 12, mr: 10, mu: 11, md: 12)
└── Model trained on: 45 samples (accuracy: 82.0%)  ← Новое!
```

### Детали:

#### 1. **Training samples** (текущее количество)
- Показывает **общее количество** training samples
- Показывает **разбивку по событиям** (ml, mr, mu, md, stop)
- Обновляется при добавлении новых samples

#### 2. **Model trained on** (количество при обучении)
- Показывает **количество образцов**, на которых обучилась модель
- Показывает **точность модели** (test accuracy)
- Обновляется после каждого обучения (ручного или автоматического)

### Как обновляется:

- Автоматически при добавлении training samples
- После ручного обучения модели
- После автоматического обучения модели
- При открытии окна ML Control

### Код:

- **Метки:** 
  - `self.lbl_training_data` (строка 58) - текущие samples
  - `self.lbl_model_trained_on` (строка 62) - образцы при обучении
- **Метод обновления:** `update_status()` (строка 152-173)
- **Источник данных:** 
  - `self.ml_trainer.get_training_stats()` - текущие samples
  - `self.ml_trainer.last_training_metrics` - метрики последнего обучения

---

## 🔄 Автоматическое обновление

### История:

- ✅ Обновляется автоматически при каждом добавлении записи
- ✅ Обновляется при загрузке/очистке истории

### ML Training:

- ✅ Обновляется при добавлении training samples
- ✅ Обновляется после обучения модели
- ✅ Обновляется при открытии ML Control Form

---

## 📊 Примеры отображения

### Главное окно:

```
┌─────────────────────────────────┐
│  History Management            │
├─────────────────────────────────┤
│  File Path: [путь]             │
│  [Save] [Load] [Clear]         │
│  Records: 156                   │ ← Здесь!
└─────────────────────────────────┘
```

### ML Control Form:

```
┌─────────────────────────────────┐
│  Status                         │
├─────────────────────────────────┤
│  Model: ✓ Trained and ready    │
│  Training samples: 45           │
│    (ml: 12, mr: 10, mu: 11,     │
│     md: 12)                     │ ← Текущие samples
│  Model trained on: 45 samples   │
│    (accuracy: 82.0%)            │ ← Образцы при обучении
└─────────────────────────────────┘
```

---

## 🎯 Разница между показателями

### Training samples (текущее)
- **Что это:** Количество образцов, которые **собраны** для обучения
- **Когда меняется:** При каждом добавлении нового sample
- **Может быть больше:** Если добавили новые samples после обучения

### Model trained on (при обучении)
- **Что это:** Количество образцов, на которых **обучилась** модель
- **Когда меняется:** Только после обучения модели
- **Фиксируется:** На момент последнего обучения

### Пример:

```
1. Собрали 40 samples → Training samples: 40
2. Обучили модель → Model trained on: 40 samples
3. Добавили ещё 5 samples → Training samples: 45
4. Model trained on: 40 samples (не изменилось!)
5. Обучили снова → Model trained on: 45 samples (обновилось!)
```

---

## 🔧 Технические детали

### История:

**Файл:** `ui/main_window.py`

```python
# Метка
self.lbl_counter = QLabel("0")  # Строка 317

# Обновление
def update_counter(self):
    self.lbl_counter.setText(str(self.history_service.count()))
```

### ML Training:

**Файл:** `ui/ml_control_form.py`

```python
# Метки
self.lbl_training_data = QLabel("Training samples: 0")  # Строка 58
self.lbl_model_trained_on = QLabel("Model trained on: -")  # Строка 62

# Обновление
def update_status(self):
    # Текущие samples
    stats = self.ml_trainer.get_training_stats()
    total = sum(stats.values())
    self.lbl_training_data.setText(f"Training samples: {total}")
    
    # Образцы при обучении
    if self.ml_trainer.last_training_metrics:
        n_samples = self.ml_trainer.last_training_metrics['n_samples']
        accuracy = self.ml_trainer.last_training_metrics['test_accuracy']
        self.lbl_model_trained_on.setText(
            f"Model trained on: {n_samples} samples (accuracy: {accuracy:.1%})"
        )
```

---

## 📝 Примечания

1. **История** показывает все записи (с событиями и без)
2. **Training samples** показывает только образцы для ML (с событиями)
3. **Model trained on** показывает количество образцов на момент обучения
4. После автоматического обучения оба показателя обновляются автоматически

---

**Версия:** 1.0  
**Дата:** 20.01.2026  
**Статус:** ✅ Документировано
