FROM python:3.13-slim

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

COPY . .

CMD ["python3", "bot.py"]
