# 使用Python 3.8 slim镜像（支持stackstorm_client==0.1.1）
FROM python:3.8-slim

# 安装系统依赖（stackstorm_client需要gcc、libssl-dev等）
RUN apt-get update && apt-get install -y --no-install-recommends gcc libssl-dev && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装Python依赖
COPY ai-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY ai-service/app.py ai-service/fault_classifier.py ai-service/knowledge_base.py ai-service/model_scheduler.py /app/
COPY ai-service/agent /app/agent
COPY blockchain /app/blockchain

# 暴露端口并启动应用
EXPOSE 8002
CMD ["python", "app.py"]
