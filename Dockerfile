FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN chmod +x wait-for-it.sh && pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["./wait-for-it.sh", "db:3306", "--", "python", "app.py"]
