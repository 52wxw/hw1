FROM node:lts-alpine AS build
WORKDIR /app

# 安装依赖并构建生产静态资源
COPY package*.json ./
RUN npm install --silent

# 先复制配置文件
COPY vue.config.js ./

# 复制 public 目录
COPY public ./public

# 复制 src 目录
COPY src ./src

# 运行构建
RUN npm run build

# 使用 Nginx 作为静态资源服务器
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

