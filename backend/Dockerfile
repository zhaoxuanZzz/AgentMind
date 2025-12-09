FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
# gcc/g++: 编译某些Python包的C/C++扩展（如chromadb、cryptography）
# postgresql-client: 可选，提供psql等数据库调试工具
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements并安装Python依赖
COPY requirements.txt .

# 使用清华镜像源加速pip安装
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

