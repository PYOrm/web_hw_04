
FROM python:3.12
LABEL authors="PYOrm"

ENV APP_HOME /app

WORKDIR $APP_HOME

COPY poetry.lock $APP_HOME/poetry.lock
COPY pyproject.toml $APP_HOME/pyproject.toml

RUN pip install poetry

COPY . .

EXPOSE 3000

CMD ["python", "main.py"]

