FROM python:3.11.3-bullseye

WORKDIR /app
RUN echo 'APT::Keep-Downloaded-Packages "false";' \
      > /etc/apt/apt.conf.d/01disable-cache
RUN apt-get update && apt-get install -y libreoffice-writer libreoffice-java-common unoconv tesseract-ocr-rus default-jre
COPY ./build/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary --upgrade -r requirements.txt
RUN pip uninstall -y pymorphy2-dicts-ru pymorphy2
RUN pip install --no-cache-dir --prefer-binary --upgrade pymorphy3
COPY . .
# fixed for python3.11
WORKDIR /app/modules/thirdparty/pymorphy2-1.2.0/
RUN python3 setup.py install

WORKDIR /app
RUN sed -i 's/env //' /usr/bin/unoconv

COPY common ./common

CMD [ "gunicorn", "-w", "2", "--bind", "0.0.0.0:8000", "app:app" ]
