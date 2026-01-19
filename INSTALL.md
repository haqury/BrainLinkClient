# Инструкция по установке BrainLink Client

## Быстрая установка

### Windows

1. Убедитесь, что установлен Python 3.8 или выше:
```cmd
python --version
```

2. Создайте виртуальное окружение:
```cmd
python -m venv venv
```

3. Активируйте виртуальное окружение:
```cmd
venv\Scripts\activate
```

4. Установите зависимости:
```cmd
pip install -r requirements.txt
```

5. Запустите приложение:
```cmd
python main.py
```

### Linux

1. Убедитесь, что установлен Python 3.8 или выше:
```bash
python3 --version
```

2. Установите системные зависимости:
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5 libbluetooth-dev

# Fedora
sudo dnf install python3-qt5 bluez-libs-devel
```

3. Создайте виртуальное окружение:
```bash
python3 -m venv venv
```

4. Активируйте виртуальное окружение:
```bash
source venv/bin/activate
```

5. Установите зависимости:
```bash
pip install -r requirements.txt
```

6. Запустите приложение:
```bash
python main.py
```

### macOS

1. Убедитесь, что установлен Python 3.8 или выше:
```bash
python3 --version
```

2. Установите Homebrew (если еще не установлен):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

3. Создайте виртуальное окружение:
```bash
python3 -m venv venv
```

4. Активируйте виртуальное окружение:
```bash
source venv/bin/activate
```

5. Установите зависимости:
```bash
pip install -r requirements.txt
```

6. Запустите приложение:
```bash
python main.py
```

## Устранение проблем при установке

### PyQt5 не устанавливается

**Решение для Windows:**
```cmd
pip install PyQt5 --no-cache-dir
```

**Решение для Linux:**
Установите из системного менеджера пакетов:
```bash
sudo apt-get install python3-pyqt5
```

### Ошибки Bluetooth на Linux

Убедитесь, что у пользователя есть права на использование Bluetooth:
```bash
sudo usermod -a -G bluetooth $USER
```

Перезагрузите систему после этого.

### Проблемы с pynput

Если возникают ошибки с pynput, установите его отдельно:
```bash
pip install pynput --upgrade
```

На Linux может потребоваться установка дополнительных пакетов:
```bash
sudo apt-get install python3-xlib
```

### Проблемы с numpy

Если numpy не устанавливается, попробуйте:
```bash
pip install numpy --upgrade --force-reinstall
```

## Создание исполняемого файла

### Windows (PyInstaller)

1. Установите PyInstaller:
```cmd
pip install pyinstaller
```

2. Создайте исполняемый файл:
```cmd
pyinstaller --onefile --windowed --name BrainLinkClient main.py
```

Исполняемый файл будет в папке `dist/`

### Создание ярлыка (Windows)

1. Создайте файл `run.bat` в корне проекта:
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python main.py
pause
```

2. Создайте ярлык для `run.bat` на рабочем столе

## Настройка устройства BrainLink

1. Включите BrainLink устройство
2. Убедитесь, что Bluetooth включен на компьютере
3. Запустите приложение
4. Нажмите "Start & Connect"
5. Выберите устройство из списка
6. Нажмите "Connect"

## Проверка установки

После установки проверьте работу:

```python
# test_installation.py
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

app = QApplication(sys.argv)
QMessageBox.information(None, "Test", "PyQt5 работает!")
sys.exit(0)
```

Запустите:
```bash
python test_installation.py
```

Если появилось окно с сообщением - установка прошла успешно!
