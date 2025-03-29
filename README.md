# FastAPI Yandex Audio Uploader

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL_16-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Сервис на FastAPI для загрузки аудио-файлов пользователями с аутентификацией через Яндекс OAuth. Использует SQLAlchemy для асинхронной работы с базой данных PostgreSQL и Docker для легкого развертывания.

## Особенности

*   **Аутентификация через Яндекс:** Вход в систему с использованием учетной записи Яндекса.
*   **Внутренняя аутентификация JWT:** Использование Access и Refresh токенов для доступа к защищенным эндпоинтам API.
*   **Загрузка аудиофайлов:** Пользователи могут загружать аудиофайлы (mp3, wav, ogg, aac, flac), опционально указывая имя файла.
*   **Управление файлами:** Получение списка своих файлов, информации о конкретном файле и удаление файлов.
*   **Управление пользователями:**
    *   Получение и обновление информации о своем профиле.
    *   Административные эндпоинты (только для суперпользователя) для просмотра, обновления и удаления пользователей.
*   **Асинхронность:** Полностью асинхронный код с использованием `async/await`, `asyncpg`, `aiofiles`, `httpx`.
*   **База данных:** PostgreSQL 16 с миграциями через Alembic.
*   **Docker:** Полностью контейнеризированное приложение (App, DB, Migrations) с использованием Docker Compose.
*   **Локальное хранилище:** Файлы сохраняются на локальном диске сервера в папку `uploads`, структурированную по ID пользователя.
*   **Автоматическая документация API:** Swagger UI (`/docs`) и ReDoc (`/redoc`).

## Технологический стек

*   **Backend:** FastAPI, Uvicorn
*   **База данных:** PostgreSQL 16
*   **ORM / DB Driver:** SQLAlchemy (asyncio), asyncpg
*   **Миграции:** Alembic
*   **Аутентификация:** python-jose (JWT), httpx (для OAuth)
*   **Работа с файлами:** aiofiles
*   **Валидация данных:** Pydantic
*   **Контейнеризация:** Docker, Docker Compose
*   **Зависимости:** Управляются через `requirements.txt`

## Предварительные требования

*   **Docker:** [Установите Docker](https://docs.docker.com/get-docker/)
*   **Docker Compose:** Обычно устанавливается вместе с Docker Desktop. Если нет, [установите Docker Compose](https://docs.docker.com/compose/install/).
*   **Git:** Для клонирования репозитория.

## Начало работы

### 1. Клонирование репозитория

```bash
git clone https://github.com/ZoomL-Olymp/fastapi-audio-upload
cd fastapi-audio-upload
```

### 2. Настройка переменных окружения (`.env`)

Создайте файл `.env` в корневой директории проекта, скопировав содержимое из `example.env` или создав его вручную. Заполните необходимые значения:

```dotenv
# Настройки проекта
PROJECT_NAME=FastAPI Yandex Audio Uploader
API_V1_STR=/api/v1

# Настройки PostgreSQL (должны совпадать с docker-compose.yml)
POSTGRES_SERVER=db # Имя сервиса БД в docker-compose
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=audio_db

# Настройки JWT
# Сгенерируйте секретный ключ, например, с помощью: openssl rand -hex 32
SECRET_KEY=ВАШ_СУПЕР_СЕКРЕТНЫЙ_КЛЮЧ_JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# Настройки Yandex OAuth 2.0 (см. следующий шаг)
YANDEX_CLIENT_ID=ВАШ_YANDEX_CLIENT_ID
YANDEX_CLIENT_SECRET=ВАШ_YANDEX_CLIENT_SECRET
# Убедитесь, что этот URI совпадает с тем, что вы укажете в настройках приложения Яндекса!
YANDEX_REDIRECT_URI=http://localhost:8000/api/v1/auth/yandex/callback

# Настройки суперпользователя (опционально)
# Укажите Yandex ID первого пользователя, который должен стать суперпользователем
FIRST_SUPERUSER_YANDEX_ID=

# Настройки загрузки файлов
UPLOAD_DIR=uploads
```

**Важно:** Обязательно сгенерируйте надежный `SECRET_KEY`.

### 3. Настройка приложения Yandex OAuth 2.0

1.  Перейдите в [Консоль разработчика Яндекса OAuth](https://oauth.yandex.ru/).
2.  Создайте новое приложение:
    *   **Название:** Произвольное (например, "FastAPI Audio Uploader").
    *   **Платформы:** Выберите "Веб-сервисы".
    *   **Redirect URI:** В поле "Callback URI №1" **обязательно** укажите значение из вашего `.env` файла (`YANDEX_REDIRECT_URI`). Например: `http://localhost:8000/api/v1/auth/yandex/callback`. **URI должен совпадать точно.**
    *   **Доступы:** Выберите необходимые права. Для текущей реализации достаточно:
        *   `login:info` (Доступ к логину, имени и фамилии, полу, аватарке)
        *   `login:email` (Доступ к адресу электронной почты по умолчанию)
3.  После создания приложения скопируйте его **Client ID** и **Client Secret**.
4.  Вставьте полученные **Client ID** и **Client Secret** в ваш `.env` файл в поля `YANDEX_CLIENT_ID` и `YANDEX_CLIENT_SECRET`.

### 4. Сборка и запуск с Docker Compose

Выполните команду в корневой директории проекта:

```bash
docker-compose up -d --build
```

Эта команда:
*   Соберет Docker-образы для сервисов `app` и `migrations` (если они еще не собраны или изменился `Dockerfile`/код).
*   Запустит контейнеры для базы данных (`db`), приложения (`app`) и сервиса миграций (`migrations`) в фоновом режиме (`-d`).
*   Сервис `migrations` дождется готовности базы данных и автоматически применит все необходимые миграции Alembic (`alembic upgrade head`).
*   Приложение будет доступно по адресу `http://localhost:8000`.
*   Папка `uploads` будет смонтирована из хост-системы в контейнер `app`.

### Остановка сервисов

Чтобы остановить все запущенные контейнеры:

```bash
docker-compose down
```

Эта команда остановит и удалит контейнеры, но сохранит данные PostgreSQL в volume (`postgres_data`), если вы не удалите его вручную.

## Документация API (Swagger/ReDoc)

После запуска приложения документация API будет доступна по следующим адресам:

*   **Swagger UI:** `http://localhost:8000/docs`
*   **ReDoc:** `http://localhost:8000/redoc`

Через Swagger UI вы можете интерактивно взаимодействовать с API, включая процесс аутентификации через Yandex и выполнение защищенных запросов.

## Использование API

1.  **Аутентификация:** Перейдите по адресу `http://localhost:8000/api/v1/auth/login/yandex` в браузере. Вас перенаправит на страницу входа Яндекса.
2.  **Авторизация:** Войдите в свою учетную запись Яндекса и разрешите приложению доступ.
3.  **Получение токенов:** Вас перенаправит обратно на `YANDEX_REDIRECT_URI`, и API вернет вам `access_token` и `refresh_token`.
4.  **Доступ к защищенным эндпоинтам:** Используйте полученный `access_token` в заголовке `Authorization` для доступа к защищенным ресурсам:
    ```
    Authorization: Bearer <ваш_access_token>
    ```
5.  **Обновление токена:** Когда `access_token` истечет, используйте `refresh_token` для получения новой пары токенов через эндпоинт `/api/v1/auth/refresh-token` (отправляя `refresh_token` в заголовке `Authorization: Bearer <ваш_refresh_token>`).

## Примеры использования (curl)

Ниже приведены примеры использования некоторых ключевых эндпоинтов API с помощью `curl`.

**Предпосылки:**

*   Вы уже прошли аутентификацию через Яндекс в браузере (перейдя по `http://localhost:8000/api/v1/auth/login/yandex`) и получили свои `access_token` и `refresh_token`.
*   Замените плейсхолдеры `YOUR_ACCESS_TOKEN`, `YOUR_REFRESH_TOKEN` и `/path/to/your/audio.mp3` на ваши реальные значения.
*   Примеры используют `^` (для `cmd`) или `` ` `` (для `PowerShell`) для переноса строк. Если вы вводите команду в одну строку, удалите эти символы.

**1. Получение информации о текущем пользователе (`/api/v1/users/me`)**

```bash
curl -X GET ^
     -H "accept: application/json" ^
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
     http://localhost:8000/api/v1/users/me
```

**2. Загрузка аудиофайла (`/api/v1/audio/upload`)**

*   Замените `/path/to/your/audio.mp3` на путь к вашему файлу.
*   Замените `audio/mpeg` на правильный MIME-тип вашего файла (например, `audio/wav`, `audio/ogg` и т.д.).
*   Опционально: передайте имя файла с помощью поля `file_name`.

```bash
curl -X POST ^
     -H "accept: application/json" ^
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
     -F "file=@/path/to/your/audio.mp3;type=audio/mpeg" ^
     -F "file_name=MyCoolTrack.mp3" ^
     http://localhost:8000/api/v1/audio/upload
```

**3. Получение списка аудиофайлов пользователя (`/api/v1/audio/`)**

```bash
curl -X GET ^
     -H "accept: application/json" ^
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
     http://localhost:8000/api/v1/audio/
```

**4. Обновление Access Token с помощью Refresh Token (`/api/v1/auth/refresh-token`)**

```bash
curl -X POST ^
     -H "accept: application/json" ^
     -H "Authorization: Bearer YOUR_REFRESH_TOKEN" ^
     http://localhost:8000/api/v1/auth/refresh-token
```
*(Обратите внимание: здесь в заголовке `Authorization` используется **Refresh Token**)*

## Структура проекта

```
.
├── alembic/              # Конфигурация и скрипты миграций Alembic
│   ├── versions/         # Файлы миграций
│   └── env.py            # Скрипт окружения Alembic
├── app/                  # Основной код приложения
│   ├── api/              # Модули API (роутеры, эндпоинты)
│   │   └── v1/
│   │       ├── endpoints/ # Файлы с эндпоинтами (auth, users, audio)
│   │       └── api.py     # Главный роутер для /api/v1
│   ├── core/             # Конфигурация, безопасность
│   ├── crud/             # Функции для взаимодействия с БД (Create, Read, Update, Delete)
│   ├── db/               # Настройка БД, сессии, базовая модель
│   ├── models/           # Модели SQLAlchemy (таблицы БД)
│   ├── schemas/          # Модели Pydantic (валидация данных, сериализация)
│   ├── __init__.py
│   ├── deps.py           # Зависимости FastAPI (get_db, get_current_user)
│   └── main.py           # Точка входа FastAPI приложения
├── uploads/              # Директория для хранения загруженных файлов (монтируется в Docker)
├── .env                  # Переменные окружения (не добавлять в Git!)
├── .gitignore            # Файлы и папки, игнорируемые Git
├── alembic.ini           # Конфигурация Alembic
├── docker-compose.yml    # Конфигурация Docker Compose
├── Dockerfile            # Инструкции для сборки Docker-образа приложения
├── LICENSE               # Файл лицензии
└── requirements.txt      # Зависимости Python
```

## Лицензия

Этот проект лицензирован под условиями лицензии MIT. См. файл [LICENSE](LICENSE) для деталей.
