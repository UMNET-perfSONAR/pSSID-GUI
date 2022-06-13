# pull official base image
FROM python:3.8.3-alpine

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy project
COPY . .

# build frontend
RUN apk add --update npm
RUN npm --prefix main/main_spa ci
RUN npm --prefix main/main_spa run build -- --mode staging 

# FIXME: should be pulled from an out-of-tree file
ENV SECRET_KEY asdfasdf

# build backend dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python3 manage.py collectstatic --no-input
RUN python3 manage.py makemigrations
RUN python3 manage.py migrate --run-syncdb

# TODO: build shouldn't occur in the same container being deployed
# but for now doing so makes reproducing easy with git clone ... && ./build_all
