

sudo systemctl start mongod

python3 app.py

touch Dockerfile
Copy from https://github.com/PrateekKumar1709/Docker-Demo/blob/main/cat-gif-app/single-container/Dockerfile

docker build -t flask-app .

docker run -p 5050:5050 flask-app

### Compose
https://hub.docker.com/_/mongo
https://github.com/docker/compose

docker compose up

docker compose down

### Docker Pull
docker tag flask-app yuwei2002/flask-todo-app:latest
docker push yuwei2002/flask-todo-app:latest

### Minikube
minikube start

kubectl apply -f app-cloud.yaml
kubectl apply -f mongo-cloud.yaml

kubectl get deployments 
kubectl get pods

(link)
minikube service flask-app

kubectl port-forward service/flask-app 8080:80 -n default

kubectl delete deployments --all
minikube stop
