FROM node:lts-alpine as build-frontend

WORKDIR /app

# get dependencies
COPY main/main_spa/package.json main/main_spa/package.json
COPY main/main_spa/package-lock.json main/main_spa/package-lock.json
COPY main/main_spa/yarn.lock main/main_spa/yarn.lock
RUN npm --prefix main/main_spa ci

# build frontend
COPY main/main_spa main/main_spa
RUN npm --prefix main/main_spa run build -- --mode staging 

# pull official base image
FROM python:3.8.3-alpine

# set work directory
WORKDIR /app

# copy in frontend stuff
COPY --from=build-frontend /app/main/static main/static
COPY --from=build-frontend /app/main/templates main/templates

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# FIXME: should be pulled from an out-of-tree file
ENV SECRET_KEY asdfasdf

# build backend dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# set up backend
COPY . .
RUN python3 manage.py collectstatic --no-input
RUN python3 manage.py makemigrations
RUN python3 manage.py migrate --run-syncdb

# TODO: build shouldn't occur in the same container being deployed
# but for now doing so makes reproducing easy with git clone ... && ./build_all
