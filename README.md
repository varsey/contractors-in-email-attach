Parses contractor information from email attachment and returns it as json

## docker-compose
* .env file with SERVER, EMAIL, PASS params
from 'build' directory:
* sudo docker compose -f docker-compose.yaml up --build

## local docker run
# sudo apt install -y default-jre libleptonica-dev libreoffice-java-common libreoffice-writer  \
    libtesseract-dev poppler-utils python3-pil tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus  \
    tesseract-ocr-script-latn unoconv
* sudo docker build --force-rm -t api-contactor-parser -f ./build/Dockerfile .
* sudo docker run -p 8000:8000 -e EMAIL=$EMAIL -e PASS=$PASS -e SERVER=$SERVER api-contactor-parser:version-tag
* curl http://0.0.0.0:8000/api/parsing?mid=02e901d9897e$a9e08ad0$fda1a070$@timer73.ru

## health checker
* .env file with SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL params
* python3 health_checker.py