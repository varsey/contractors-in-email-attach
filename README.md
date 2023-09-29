* sudo docker build --force-rm -t api-contactor-parser -f ./build/Dockerfile . 
* sudo docker tag api-contactor-parser:latest <selector>/api-contactor-parser:v0.1
* sudo docker push <selector>/api-contactor-parser:v0.2
* sudo docker run -p 8000:8000 -e EMAIL=$EMAIL -e PASS=$PASS -e SERVER=$SERVER <selector>/api-contactor-parser:v0.2
* curl http://0.0.0.0:8000/api/parse/02e901d9897e\$a9e08ad0\$fda1a070\$@timer73.ru/
* curl http://0.0.0.0:8000/api/parsing?mid=02e901d9897e$a9e08ad0$fda1a070$@timer73.ru

## docker-compose
* sudo docker-compose -f docker-compose.yaml up --build
