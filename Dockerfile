FROM python:3
MAINTAINER Jacques Supcik <jacques@supcik.net>

RUN mkdir /app
ADD *.py /app/
ADD requirements.txt /app/
ADD LICENSE /app/

WORKDIR /app
RUN pip3 install -r requirements.txt

ENV USER=root

EXPOSE 8000

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0", "groople-doc:app"]
