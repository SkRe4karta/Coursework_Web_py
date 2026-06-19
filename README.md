# Peregovorki — Веб-приложение для бронирования переговорных комнат

Тема проекта: «Разработка веб-приложения для бронирования переговорных комнат в офисе с календарём занятости, системой уведомлений и аналитикой загрузки комнат».

Peregovorki — это классическое серверное веб-приложение на Python (Flask), разработанное в качестве курсового проекта. Система предназначена для оптимизации использования переговорных комнат в офисе: сотрудники могут бронировать комнаты, отслеживать занятость через интерактивный календарь и получать уведомления, а администраторы — управлять структурой комнат, анализировать загрузку и выгружать отчеты.

---

## 🛠 Стек технологий

* **Backend**: Python 3.11+, Flask, Flask-SQLAlchemy, SQLAlchemy, Flask-Login.
* **База данных**: PostgreSQL (основная), SQLite (встроенный fallback-вариант для локального тестирования).
* **Секьюрити**: Хэширование паролей с помощью `werkzeug.security`.
* **Frontend**: Шаблонизатор Jinja2, HTML5, CSS3 (адаптивная верстка, Glassmorphism, светлые зеленые тона), чистый JavaScript.
* **Иконки & Интерактивы**: FontAwesome (CDN), Chart.js (для графиков аналитики).
* **Экспорт данных**: ReportLab (генерация PDF отчетов), стандартный модуль Python `csv` (выгрузка CSV).

---

## 🌟 Основные возможности

1. **Ролевой доступ**:
   * **Root (Владелец)**: Полный аудит системы, назначение ролей администраторов, блокировка пользователей, управление правами.
   * **Admin (Администратор)**: Управление комнатами и бронированиями, просмотр аналитики, выгрузка отчетов. Доступные модули зависят от прав, выданных Root.
   * **User (Сотрудник)**: Просмотр комнат с фильтрацией по вместимости/оборудованию, интерактивный календарь, создание/редактирование/отмена своих броней.
2. **Предотвращение конфликтов (Overlap Check)**:
   * Система автоматически сверяет интервалы времени при бронировании. Не допускаются пересечения броней для одной и той же комнаты.
3. **Умный подбор комнат**:
   * Алгоритм автоматического поиска и рекомендации оптимальной переговорной на основе времени, вместимости, оборудования и расположения.
4. **Аналитика загрузки**:
   * Страница с интерактивными графиками распределения броней по дням недели, популярности комнат и активности сотрудников.
5. **Уведомления через БД**:
   * Создание внутренних уведомлений при приглашении на встречу, редактировании или отмене бронирования. Без использования внешнего SMTP.
6. **Экспорт**:
   * Выгрузка таблицы встреч в формате CSV.
   * Формирование структурированного PDF-отчета со статистикой по загрузке.
7. **Загрузка файлов**:
   * Безопасное сохранение файлов, прикрепленных к бронированию, с генерацией уникальных имен.

---

## 📂 Структура проекта

```text
peregovorki/
├── app/                      # Исходный код приложения
│   ├── __init__.py           
│   ├── models.py             
│   ├── utils.py              
│   ├── auth.py               
│   ├── rooms.py              
│   ├── booking.py            
│   ├── admin.py              
│   ├── root.py               
│   ├── analytics.py          
│   ├── reports.py            
│   ├── static/               # Статические ресурсы (CSS, JS)
│   ├── templates/            # HTML-шаблоны Jinja2
│   └── uploads/              # Директория загрузки пользовательских вложений
├── deploy/                   # Примеры конфигураций для VPS
├── instance/                 # Системная папка для локальной SQLite БД
├── config.py                 # Конфигурационный файл Flask
├── requirements.txt          # Зависимости Python
├── init_db.py                # Скрипт инициализации таблиц БД
├── seed.py                   # Заполнение БД тестовыми данными
├── wsgi.py                   # Точка входа для Gunicorn
├── run.py                    # Запуск локального сервера
├── .env.example              # Пример настроек окружения
└── README.md                 # Документация проекта
```

---

## 🚀 Команды для локального запуска

Приложение может работать как с **PostgreSQL**, так и с **SQLite** (fallback-вариант).

### 1. Клонирование и настройка окружения
Откройте терминал в папке проекта.

**На Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**На Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка подключения к базе данных
Скопируйте настройки из `.env.example` в новый файл `.env`:
Если вы хотите использовать **PostgreSQL**, создайте БД и пропишите путь в `.env`:
```text
SECRET_KEY=change-me
DATABASE_URL=postgresql://postgres:password@localhost:5432/peregovorki
FLASK_ENV=development
UPLOAD_FOLDER=app/uploads
```

### 3. Инициализация и наполнение БД (Seed-данные)
Запустите скрипты для генерации таблиц и наполнения базы:

> [!WARNING]
> **Скрипт `seed.py` производит полный сброс схемы базы данных (`db.drop_all()`) перед заполнением!** 
> Ни в коем случае не запускайте данный скрипт на боевой (production) базе данных во избежание безвозвратной потери данных. Для защиты боевых серверов в скрипт встроен интерактивный предохранитель, который блокирует автоматическое выполнение и требует явного подтверждения в не-development/PostgreSQL средах.

```bash
python init_db.py
python seed.py
```

### 4. Запуск сервера
Запустите приложение:
```bash
python run.py
```
Браузер: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔑 Данные тестовых пользователей (демо-аккаунты)

После `python seed.py` доступны:

1. **Главный администратор (Root)**:
   * **Email**: `root@example.com` | **Пароль**: `root123`
2. **Дежурный администратор (Admin)**:
   * **Email**: `admin@example.com` | **Пароль**: `admin123`
3. **Сотрудник офиса (User)**:
   * **Email**: `user@example.com` | **Пароль**: `user123`

---

## 📦 Подготовка к деплою на VPS (Ubuntu Linux)

### 1. Команды Git (Подготовка к GitHub)
```bash
git init
git add .
git commit -m "Финальная версия курсовой работы"
git branch -M main
git remote add origin <URL вашего репозитория>
git push -u origin main
```

### 2. Настройка PostgreSQL на сервере
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -i -u postgres
psql
CREATE DATABASE peregovorki;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE peregovorki TO postgres;
\q
exit
```

### 3. Конфигурация Systemd службы для Gunicorn
Пример доступен в `deploy/peregovorki.service.example`. Скопируйте его:
```bash
sudo cp deploy/peregovorki.service.example /etc/systemd/system/peregovorki.service
sudo systemctl daemon-reload
sudo systemctl start peregovorki
sudo systemctl enable peregovorki
```

### 4. Конфигурация Nginx
Пример доступен в `deploy/nginx.conf.example`.
```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/peregovorki
sudo ln -s /etc/nginx/sites-available/peregovorki /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```
Приложение будет доступно по IP-адресу или домену вашего VPS.
