FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --chown=node:node package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY --chown=node:node . .
USER node
EXPOSE 3000
CMD ["node", "index.js"]