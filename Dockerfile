FROM python:3.7

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

COPY redmine_exporter.py /usr/src/app

EXPOSE 9121
ENV REDMINE_SERVER=http://redmine:8080 VIRTUAL_PORT=9121 DEBUG=0

ENTRYPOINT [ "python", "-u", "./redmine_exporter.py" ]
