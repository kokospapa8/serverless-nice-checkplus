# Serverless nice 체크 플러스


https://www.niceid.co.kr/prod_mobile.nc
나이스 휴대폰 본인확인 샘플을 AWS SAM을 이용해 서버리스로 사용할 수 있도록 패키징했음

python 예제 링크

MAC ->
## setup
aws configure 

pip env 3.8 
pip install -> 

sam install

env setting


 
## deploy
## check

$ sudo chmod 755 checkplus/CPClient_64bit 

$ sam local invoke -e events/event.json       

$ sam build 
$ sam deploy --guided

