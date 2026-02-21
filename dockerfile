FROM python:3.12-trixie

COPY main.py app/
COPY /assets app/assets/
COPY requirements.txt app/

RUN pip install -r app/requirements.txt

CMD ["python3","app/main.py"]
