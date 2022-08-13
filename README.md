![workflow](https://github.com/garmagelm/foodgram-project-react/actions/workflows/foodgram_project.yml/badge.svg)
# Проект: Foodgram
Приложение для публикации, редактирования и добавления в избранное рецептов с функцией "корзина покупок", которая предоставляет список покупок для всех выбранных рецептов.

Работает на базе Django & React.

Пример развернутого проекта можно посмотреть http://51.250.18.26/

***Установка:***
1. Устанавливаем [Docker](https://docs.docker.com/engine/install/).
2. Клонируем репозитарий из GitHub командой в терминале 
```bash
git clone git@github.com:Thx-Phila/foodgram-project-react.git
```

***Настройка переменного окружения .env:***

* Создаем виртуальное окружение командой 
```bash
python3 -m venv venv
```
* Создаем файл .env
* Вводим значения секретов: 
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=<название вашей базы данных>
POSTGRES_USER=<имя пользователя в postgres>
POSTGRES_PASSWORD=<пароль пользователя>
DB_HOST=db  # Сюда можете прописать localhost, либо оставить, если будете использовать docker-compose
DB_PORT=5432
```

***Команды для Docker***
1. Запускаем контейнер из папки infra командой
```bash
docker-compose up --build -d
```
2. Выполняем миграцию командой 
```bash
docker-compose exec backend python manage.py migrate --noinput
```
3. Создаем суперпользователя 
```bash
docker-compose exec backend python manage.py createsuperuser
```
4. Собераем файлы статики в одну директорию: 
```bash
docker-compose exec backend python manage.py collectstatic --no-input
```
5. В backend создаем фикстуры 
```bash
docker-compose exec backend python manage.py loaddata ingredients.json
```
6. Команда для остановки запущенных docker-контейнеров и удаление их:
```bash
docker-compose down
```

***Стек технологий:***

* Python3
* Django
* Django REST Framework
* Docker Desktop
* Posgresql

***Автор проекта:***
Ворончихин Яков