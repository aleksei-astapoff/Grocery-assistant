## Описание
# Продуктовый помощник Grocery assistant.

![Foodgram workflow](https://github.com/aleksei-astapoff/foodgram-project-react/actions/workflows/main.yml/badge.svg)


Пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное»,скачивать сводный список продуктов

Cайт доступен по ссылке https://duck8000.hopto.org/

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

7. ### Можно выполнить базовые загрузки перед этим создав  файл ENV в папке infra  заполнив его по примеру env.example :
```
python manage.py foodgramsuperuser

python manage.py load_ingredients
```

8. ### Запустите локальный сервер:
```
python manage.py runserver
```


## Локальный запуск проекта через Docker

1. ### Установите docker согласно [инструкции](https://docs.docker.com/engine/install/ubuntu/)
Пользователям Windows нужно будет подготовить систему, установить для неё ядро Linux — и после этого установить Docker.

2. ### В корневой дирректории выполните команды:
Перед выполнением обязательно заполните файл ENV в папке infra по примеру env.example!
```
docker-compose up
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py foodgramsuperuser
docker compose exec backend python manage.py load_data
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
sudo mkdir foodgram
```

4. ### В папке kittygram создайте файл docker-compose.production.yml и скопируйте туда содержимое файла docker-compose.production.yml из проекта:
```
cd foodgram
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

7. ### Из дирректории foodgram выполнить команды:
Перед выполнением обязательно создайте и заполните файл ENV в папке foodgram по примеру env.example и переместите файл конфигурации для nginx (nginx.conf) в foodgram!
```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py foodgramsuperuser
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_ingredients
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input
```

Если необходимо создать суперпользователя:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

## Автор
[Алексей Астапов](https://github.com/aleksei-astapoff)

