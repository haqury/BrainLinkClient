# BrainLink Client - Python Edition

Python порт приложения BrainLinkConnect для управления компьютером с помощью EEG (электроэнцефалография) и гироскопа от устройства BrainLink.

## Описание

BrainLink Client - это приложение для подключения к устройству BrainLink через Bluetooth и использования данных мозговой активности (EEG) и движений головы (гироскоп) для управления курсором мыши.

## Возможности

### Основные функции
- **Подключение по Bluetooth** к устройству BrainLink
- **Чтение данных EEG**: Attention, Meditation, Delta, Theta, Alpha, Beta, Gamma волны
- **Данные гироскопа**: отслеживание движений головы (вверх/вниз/влево/вправо)
- **Управление мышью**: перемещение курсора на основе EEG паттернов
- **Запись и воспроизведение**: сохранение истории паттернов для обучения

### Дополнительные возможности
- Калибровка гироскопа для точного отслеживания
- Конфигурируемая чувствительность распознавания паттернов
- Многоуровневая система распознавания событий
- Сохранение/загрузка конфигураций и истории в JSON

## Установка

### Требования
- Python 3.8 или выше
- Windows 10/11 (для полной функциональности)

### Шаги установки

1. Клонируйте репозиторий или скопируйте файлы проекта

2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

### Запуск приложения

```bash
python main.py
```

### Основной рабочий процесс

1. **Подключение к устройству**
   - Нажмите кнопку "Start & Connect"
   - Выберите устройство BrainLink из списка
   - Нажмите "Connect"

2. **Режим обучения** (Training Mode)
   - Выберите направление (Move Left/Right/Up/Down/Stop)
   - Удерживайте клавишу со стрелкой на клавиатуре
   - Сконцентрируйтесь на действии
   - Данные автоматически сохранятся в историю

3. **Режим автоматического управления**
   - Включите "Auto Use (Direct Control)"
   - Включите "Use Key Control"
   - Приложение будет двигать курсор на основе распознанных паттернов

4. **Конфигурация**
   - Нажмите "Config Fault" для настройки чувствительности
   - Установите допуски для каждого параметра EEG
   - Сохраните конфигурацию в файл

5. **Управление историей**
   - "Save to File" - сохранить историю обучения
   - "Load from File" - загрузить ранее сохраненную историю
   - "Clear" - очистить текущую историю

### Использование гироскопа

1. Откройте окно "Gyro"
2. Нажмите "Calibrate" для установки центрального положения
3. Включите "Use Gyro for Control"
4. Двигайте головой для управления курсором

## Структура проекта

```
BrainLinkClient/
│
├── models/                  # Модели данных
│   ├── eeg_models.py       # EEG данные и конфигурация
│   ├── gyro_models.py      # Данные гироскопа
│   └── system_models.py    # Системная информация
│
├── services/               # Сервисные компоненты
│   ├── brainlink_sdk_wrapper.py  # Обертка для C# DLL (опционально)
│   ├── device_simulator.py       # Симулятор устройства для тестов
│   ├── history_service.py        # Управление историей
│   ├── head_tracker_service.py   # Отслеживание движений головы
│   ├── mouse_service.py          # Управление мышью
│   └── system_service.py         # Системные функции
│
├── ui/                     # Пользовательский интерфейс
│   ├── main_window.py      # Главное окно
│   ├── connect_form.py     # Окно подключения (использует PyBrainLink)
│   ├── eeg_data_form.py    # Отображение EEG данных
│   ├── gyro_form.py        # Окно гироскопа
│   ├── config_form.py      # Конфигурация
│   └── styles.py           # Темная тема оформления
│
├── main.py                 # Точка входа в приложение
├── requirements.txt        # Зависимости Python (включая PyBrainLink)
└── README.md              # Этот файл
```

> **Примечание**: Bluetooth подключение и парсинг данных вынесены в отдельную библиотеку [PyBrainLink](https://github.com/haqury/pybrainlink)

## Технологии

- **PyQt5** - графический интерфейс
- **[PyBrainLink](https://github.com/haqury/pybrainlink)** - библиотека для работы с BrainLink устройствами
- **bleak** - Bluetooth Low Energy подключение (через PyBrainLink)
- **pyautogui** - управление мышью
- **pynput** - перехват клавиатуры
- **numpy** - математические операции

## PyBrainLink Library

Проект использует специализированную библиотеку **PyBrainLink** для работы с BrainLink устройствами.

### О библиотеке

PyBrainLink - это Python библиотека для подключения к BrainLink EEG устройствам через Bluetooth LE, парсинга данных и экспорта в JSON.

**Репозиторий**: https://github.com/haqury/pybrainlink

**Последний релиз**: [v0.1.0](https://github.com/haqury/pybrainlink/releases/tag/v0.1.0)

### Возможности PyBrainLink

- ✅ Асинхронное подключение через Bluetooth LE (bleak)
- ✅ Автоматический парсинг протокола BrainLink
- ✅ Модели данных для EEG, Gyro и Extended данных
- ✅ Простой API для интеграции
- ✅ Поддержка dataclasses для удобной работы с данными

### Установка

Библиотека автоматически устанавливается вместе с зависимостями проекта:

```bash
pip install git+https://github.com/haqury/pybrainlink.git@v0.1.0
```

### Пример использования

```python
from pybrainlink import BrainLinkDevice, BrainLinkModel
from dataclasses import asdict
import asyncio
import json

async def main():
    device = BrainLinkDevice()
    
    def on_eeg_data(data: BrainLinkModel):
        # Конвертировать в JSON
        json_data = json.dumps(asdict(data), indent=2)
        print(json_data)
    
    device.on_eeg_data = on_eeg_data
    
    # Подключение к устройству
    devices = await device.scan_devices(timeout=5.0)
    if devices:
        await device.connect(devices[0].address)
        await asyncio.sleep(30)  # Получать данные 30 секунд
        await device.disconnect()

asyncio.run(main())
```

### Документация

Полная документация доступна в репозитории PyBrainLink: https://github.com/haqury/pybrainlink#readme

## Отличия от C# версии

### Улучшения
- Кроссплатформенность (Windows, Linux, macOS)
- Более простая установка (pip install)
- Асинхронная работа с Bluetooth (bleak)
- Современный Python код с type hints

### Ограничения
- Требуется настройка протокола BrainLink SDK
- Bluetooth подключение может отличаться в зависимости от ОС

## Конфигурационные файлы

### История (history.json)
```json
[
  {
    "attention": 75,
    "meditation": 60,
    "delta": 120000,
    "theta": 85000,
    "low_alpha": 45000,
    "high_alpha": 35000,
    "low_beta": 25000,
    "high_beta": 20000,
    "low_gamma": 15000,
    "high_gamma": 10000,
    "event_name": "ml"
  }
]
```

### Конфигурация (config.json)
```json
{
  "attention": 10,
  "meditation": 10,
  "delta": 50000,
  "theta": 50000,
  "low_alpha": 20000,
  "high_alpha": 20000,
  "low_beta": 15000,
  "high_beta": 15000,
  "low_gamma": 10000,
  "high_gamma": 10000
}
```

## Решение проблем

### Bluetooth не находит устройства
- Убедитесь, что Bluetooth включен
- Проверьте, что BrainLink включен и заряжен
- Попробуйте перезапустить приложение

### Курсор двигается слишком быстро/медленно
- Настройте параметры в Config Fault
- Увеличьте допуски для более плавного управления
- Уменьшите допуски для более точного управления

### Паттерны не распознаются
- Убедитесь, что записано достаточно данных в истории
- Попробуйте увеличить multi_count
- Проверьте настройки чувствительности

## Разработка

### Добавление новых функций

1. Модели данных → `models/`
2. Бизнес-логика → `services/`
3. UI компоненты → `ui/`

### Работа с PyBrainLink

Для работы с BrainLink устройствами используется библиотека PyBrainLink. Все низкоуровневые операции Bluetooth и парсинг протокола реализованы в ней.

Пример интеграции в UI:

```python
from pybrainlink import BrainLinkDevice, BrainLinkModel

# Создание устройства
self.device = BrainLinkDevice()

# Установка callback для EEG данных
def on_eeg_data(data: BrainLinkModel):
    print(f"Attention: {data.attention}, Meditation: {data.meditation}")
    
self.device.on_eeg_data = on_eeg_data

# Сканирование и подключение
devices = await self.device.scan_devices(timeout=5.0)
await self.device.connect(devices[0].address)
```

### Расширение протокола BrainLink

Если нужно расширить протокол или добавить поддержку новых типов данных, создайте Pull Request в репозиторий PyBrainLink: https://github.com/haqury/pybrainlink

## Лицензия

Порт оригинального проекта BrainLinkConnect.

## Авторы

- Оригинальная версия (C#): BrainLinkConnect
- Python порт: 2026

## Поддержка

Для вопросов и предложений создавайте Issues в репозитории проекта.
