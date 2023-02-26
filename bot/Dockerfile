FROM python:3.10

RUN mkdir -p /usr/src/app/

WORKDIR /usr/src/app/

# ENV TELEGRAM_API_TOKEN = ""
# ENV TELEGRAM_PAYMENTS_PROVIDER_TOKEN = ''
# ENV TELEGRAM_CHAT_ID = ''

COPY . /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]