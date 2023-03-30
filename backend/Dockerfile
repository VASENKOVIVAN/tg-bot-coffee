FROM ubuntu

RUN mkdir -p /usr/src/app/

WORKDIR /usr/src/app/

COPY . /usr/src/app/

RUN pip install pip install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]