FROM node:16-alpine as build-frontend

WORKDIR /app

# get dependencies
COPY frontend/package.json .
COPY frontend/package-lock.json .
COPY frontend/yarn.lock .
RUN npm ci

# build frontend
COPY frontend .
RUN npm run build -- --mode staging 

# pull official base image
FROM python:3.8.3-alpine as build-backend

# set work directory
WORKDIR /app

# copy in frontend stuff
COPY --from=build-frontend /static main/static
COPY --from=build-frontend /templates main/templates

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# FIXME: should be pulled from an out-of-tree file
ENV SECRET_KEY asdfasdf

# build backend dependencies
COPY backend/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# set up backend
COPY backend backend
COPY backend/manage.py .
RUN python3 manage.py collectstatic --no-input
RUN python3 manage.py makemigrations
RUN python3 manage.py migrate --run-syncdb
