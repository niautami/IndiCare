FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
EXPOSE 8501
CMD ["streamlit", "run", "streamlitApp.py", "--server.port=8501", "--server.address=0.0.0.0"]
