FROM prefecthq/prefect:latest-python3.9

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
ENV PYTHONPATH=/app
