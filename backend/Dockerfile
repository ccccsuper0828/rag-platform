FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
# ffmpeg 是处理音频必须的
# build-essential, zlib1g-dev, libjpeg-dev 是为了编译 Pillow, zlib-state 等库
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 使用华为云镜像源，并分步执行以提高成功率
RUN pip install --upgrade pip -i https://repo.huaweicloud.com/repository/pypi/simple && \
    pip install uvicorn -i https://repo.huaweicloud.com/repository/pypi/simple && \
    pip install -r requirements.txt \
    -i https://repo.huaweicloud.com/repository/pypi/simple \
    --default-timeout=1000 \
    --trusted-host repo.huaweicloud.com

COPY . .

# 创建必要的目录
RUN mkdir -p uploads chroma_db logs/metrics rag_storage /app/external

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
