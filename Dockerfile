FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

CMD ["flask", "run"]
# Базовый образ
FROM python:3.12-slim

# Установим рабочую директорию
WORKDIR /app

# Скопируем зависимости
COPY requirements.txt .

# Установим зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Скопируем весь проект
COPY . .

# Укажем порт
EXPOSE 5000


CMD ["python", "app/app.py"]
