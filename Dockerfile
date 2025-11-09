FROM node:latest
LABEL Name=quicktype Version=0.0.1

RUN npm install -g quicktype

ENTRYPOINT ["quicktype"]