FROM mazanax/python-3.7-alpine

ENV PYTHONBUFFERED 1

WORKDIR /app

COPY . /app

RUN pip install -U pip
RUN pip install -r requirements.txt