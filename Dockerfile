# 使用輕量級 Python 映像檔
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴 (如果核心需要編譯某些東西)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案原始碼 (包含 bcsfe_web 和 src)
COPY . .

# 設定環境變數，確保 Python 能找到模組
ENV PYTHONPATH=/app
ENV PORT=8000

# 暴露連接埠
EXPOSE 8000

# 啟動指令
CMD ["python", "bcsfe_web/main.py"]
