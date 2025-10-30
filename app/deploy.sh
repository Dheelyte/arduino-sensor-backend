aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin 216673926268.dkr.ecr.eu-north-1.amazonaws.com/arduino-sensor

docker buildx build --platform linux/x86_64 -t 216673926268.dkr.ecr.eu-north-1.amazonaws.com/arduino-sensor:latest .

docker push 216673926268.dkr.ecr.eu-north-1.amazonaws.com/arduino-sensor:latest

aws lambda update-function-code --function-name arduino-sensor --image-uri "216673926268.dkr.ecr.eu-north-1.amazonaws.com/arduino-sensor:latest"
