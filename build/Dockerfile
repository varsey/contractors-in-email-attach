FROM python:3.11.5-slim-bullseye

WORKDIR /app
RUN echo 'APT::Keep-Downloaded-Packages "false";' \
      > /etc/apt/apt.conf.d/01disable-cache
RUN apt-get update && apt-get install -y libreoffice-writer libreoffice-java-common unoconv tesseract-ocr-rus \
    default-jre poppler-utils
COPY ./build/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary --upgrade -r requirements.txt
COPY . .

WORKDIR /app
RUN sed -i 's/env //' /usr/bin/unoconv

COPY common ./common

# CMD [ "python", "app.py" ]
CMD [ "gunicorn", "-w", "2", "--bind", "0.0.0.0:8000", "app:app" ]
