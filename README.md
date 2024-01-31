## Описание
# Продуктовый помощник Foodgram - дипломный проект

Пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное»,скачивать сводный список продуктов


![Kittygram workflow](https://github.com/aleksei-astapoff/kittygram_final/actions/workflows/main.yml/badge.svg)  

## Технологии

- Python
- Django
- Djangorestframework
- Djoser
- Gunicorn
- pytest
- Docker
- React (frontend)

К проекту подключена база PostgreSQL. На удаленном сервере установлена операционная система Ubuntu.


## Локальный запуск проекта

1. ### Склонируйте репозиторий:
```
git@github.com:aleksei-astapoff/foodgram-project-react.git
```

2. ### Создайте и активируйте виртуальное окружение:
Команда для установки виртуального окружения на Mac или Linux:
```
python3 -m venv env
source env/bin/activate
```

Команда для установки виртуального окружения на Windows:
```
python -m venv venv
source venv/Scripts/activate
```

3. ### В корневой дирректории создайте файл .env по образцу .env.example.

4. ### Установите зависимости:
```
cd backend
pip install -r requirements.txt
```

5. ### Проведите миграции:
```
python manage.py migrate
```

6. ### При необходимости создайте суперпользователя:
```
python manage.py createsuperuser
```

7. ### Можно выполнить базовые загрузки перед этим создав  файл ENV в папке infra  заполнив его по примеру :
```
python manage.py createsuperuser
```

8. ### Запустите локальный сервер:
```
python manage.py runserver
```


## Локальный запуск проекта через Docker

1. ### Установите docker согласно [инструкции](https://docs.docker.com/engine/install/ubuntu/)
Пользователям Windows нужно будет подготовить систему, установить для неё ядро Linux — и после этого установить Docker.

2. ### В корневой дирректории выполните команды:
```
docker-compose up
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py collectstatic
```


## Установка проекта на удалённом сервере

1. ### Выполните вход на удаленный сервер

2. ### Установите Docker Compose на сервер:
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```

3. ### Создайте папку kittygram:
```
sudo mkdir kittygram
```

4. ### В папке kittygram создайте файл docker-compose.production.yml и скопируйте туда содержимое файла docker-compose.production.yml из проекта:
```
cd kittygram
sudo touch docker-compose.production.yml 
sudo nano docker-compose.production.yml
```

5. ### В файл настроек nginx добавить домен сайта:
```
sudo nano /etc/nginx/sites-enabled/default
```

6. ### После корректировки файла nginx выполнить команды:
```
sudo nginx -t
sudo service nginx reload
```

7. ### Из дирректории kittygram выполнить команды:
```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /static/static/
```

Если необходимо создать суперпользователя:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```


## Автоматический деплой проекта на сервер.

Предусмотрен автоматический деплой проекта на сервер с помощью GitHub actions. Для этого описан workflow файл:
.github/workflows/main.yml
После деплоя в проекте предусмотрена отправка сооющения в телеграм чат.

1. ### После внесения правок в проект выполните команды:
```
git add .
git commit -m 'комментарий'
git push
```

GitHub actions выполнит необходимые команды из workflow файла - контейнеры на удаленном сервере перезапустятся.

2. ### Для правильной работы workflow необходимо добавить в Secrets репозитория на GitHub переменные окружения:
```
DOCKER_PASSWORD=<пароль от DockerHub>
DOCKER_USERNAME=<имя пользователя DockerHub>
HOST=<ip сервера>
POSTGRES_DB=<название базы данных>
POSTGRES_PASSWORD=<пароль к базе данных>
POSTGRES_USER=<пользователь базы данных>
SECRET_KEY=<секретный ключ проекта>
SSH_KEY=<ваш приватный SSH-ключ (для получения команда: cat ~/.ssh/id_rsa)>
SSH_PASSPHRASE=<пароль для сервера, если есть>
USER=<username для подключения к удаленному серверу>
TELEGRAM_TO=<id вашего Телеграм-аккаунта>
TELEGRAM_TOKEN=<токен вашего бота>
```


## Настройка защищенного протоколо HTTPS:
1. ### Установите и обновите зависимости для пакетного менеджера snap:
```
sudo snap install core; sudo snap refresh core
```

2. ### Установите пакет certbot:
```
sudo snap install --classic certbot
```

3. ### Создание ссылки на certbot в системной директории, чтобы у пользователя с правами администратора был доступ к этому пакету:
```
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

4. ### Запустите certbot:
```
sudo certbot --nginx 
```

5. ### Перезагрузите конфигурацию Nginx:
```
sudo systemctl reload nginx 
```


## Автор
[Алексей Астапов](https://github.com/aleksei-astapoff)

