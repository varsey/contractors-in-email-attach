FROM python:3.12.4-slim-bookworm

WORKDIR /app
RUN echo 'APT::Keep-Downloaded-Packages "false";' \
      > /etc/apt/apt.conf.d/01disable-cache
RUN apt-get update && apt-get install -y libreoffice-writer libreoffice-java-common unoconv tesseract-ocr-rus \
    libleptonica-dev tesseract-ocr libtesseract-dev python3-pil tesseract-ocr-eng tesseract-ocr-script-latn \
    default-jre poppler-utils && apt-get clean
COPY ./build/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary --upgrade -r requirements.txt
COPY . .

WORKDIR /app
RUN sed -i 's/env //' /usr/bin/unoconv

COPY common ./common

ENV J_XMX="3348m"
ENV J_XMS="1024m"
CMD [ "gunicorn", "-w", "2", "--bind", "0.0.0.0:8000", "app:app" ]
