FROM python:3.8.0-slim

WORKDIR /code

COPY src/requirements.txt .

RUN pip install -r requirements.txt

COPY src /code

EXPOSE 5000/tcp

COPY . /src/lifecycle_manager/

CMD python -m lifecycle_manager.app
