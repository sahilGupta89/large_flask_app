FROM python:3.7
RUN apt-get update
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV FLASK_APP api
ENV FLASK_ENV development
ENV FLASK_RUN_HOST 0.0.0.0
EXPOSE 5000
CMD ["flask", "run"]
#CMD gunicorn -b :5000 "api:create_app()" -w 4  -c gunicorn_config.py --forwarded-allow-ips="*"