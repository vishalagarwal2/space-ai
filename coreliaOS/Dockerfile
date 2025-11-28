FROM python:3.12

RUN apt update

RUN useradd -ms /bin/bash coreliaos

USER coreliaos

WORKDIR /home/coreliaos/code

COPY --chown=coreliaos:coreliaos requirements.txt .

RUN pip install --upgrade pip
RUN pip install --user -r requirements.txt  
RUN pip install --user psycopg2-binary python-dotenv whitenoise

COPY --chown=coreliaos:coreliaos .env.example .env

COPY --chown=coreliaos:coreliaos . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000
