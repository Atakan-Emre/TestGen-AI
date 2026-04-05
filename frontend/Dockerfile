FROM node:20-alpine

WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY package*.json ./
RUN npm ci --legacy-peer-deps --include=optional \
    && ARCH="$(apk --print-arch)" \
    && if [ "$ARCH" = "aarch64" ]; then npm install --no-save @rollup/rollup-linux-arm64-musl; fi \
    && if [ "$ARCH" = "x86_64" ]; then npm install --no-save @rollup/rollup-linux-x64-musl; fi

# Kaynak kodları kopyala
COPY . .

EXPOSE 5173

# Geliştirme sunucusunu başlat
CMD ["npm", "run", "dev"] 
