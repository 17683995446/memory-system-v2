FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY examples/ ./examples/

# 创建必要的目录
RUN mkdir -p data logs

# 环境变量配置
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV DATA_DIR=/app/data
ENV LOG_DIR=/app/logs

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "examples/api_server.py"]
