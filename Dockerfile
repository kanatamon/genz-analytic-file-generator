FROM tiangolo/uwsgi-nginx-flask:python3.6

ENV FLASK_ENV production
ENV LISTEN_PORT 4321

EXPOSE 4321

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY . /app

WORKDIR /app