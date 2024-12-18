FROM python:3.12.8-slim-bullseye

WORKDIR /app
RUN echo 'APT::Keep-Downloaded-Packages "false";' > /etc/apt/apt.conf.d/01disable-cache && \
    apt update &&  \
    apt install -y default-jre libleptonica-dev libreoffice-java-common libreoffice-writer  \
    libtesseract-dev poppler-utils python3-pil tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus  \
    tesseract-ocr-script-latn unoconv &&  \
    apt-get clean
COPY ./build/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary --upgrade -r requirements.txt
COPY . .

WORKDIR /app
RUN sed -i 's/env //' /usr/bin/unoconv

ENV J_XMX="3348m"
ENV J_XMS="1024m"
ENV PYTHONDONTWRITEBYTECODE=1
CMD [ "gunicorn", "-w", "2", "--bind", "0.0.0.0:8000", "app:app" ]
