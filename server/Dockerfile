FROM node:8
WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install

RUN ls -la

COPY . .
EXPOSE 8080

CMD ["npm", "start"]
