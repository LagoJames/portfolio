FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN mkdir -p uploads/projects uploads/profile uploads/cv uploads/client_files uploads/blog uploads/invoices

EXPOSE 8080

CMD ["sh", "-c", "flask db upgrade && python seed.py && exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120 wsgi:app"]
