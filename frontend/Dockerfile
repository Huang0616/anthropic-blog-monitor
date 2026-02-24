FROM registry.cn-hangzhou.aliyuncs.com/library/node:20-alpine

WORKDIR /app

# 复制 package.json
COPY package.json ./

# 安装依赖
RUN npm install --registry=https://registry.npmmirror.com

# 复制源代码
COPY . .

# 构建
RUN npm run build

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "start"]
