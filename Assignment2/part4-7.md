https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html

### Setup AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

us-east-2
aws configure

aws sts get-caller-identity

```bash
# for ARM systems, set ARCH to: `arm64`, `armv6` or `armv7`
ARCH=amd64
PLATFORM=$(uname -s)_$ARCH

curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$PLATFORM.tar.gz"

# (Optional) Verify checksum
curl -sL "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_checksums.txt" | grep $PLATFORM | sha256sum --check

tar -xzf eksctl_$PLATFORM.tar.gz -C /tmp && rm eksctl_$PLATFORM.tar.gz

sudo mv /tmp/eksctl /usr/local/bin
```

### Create cluster
eksctl create cluster --name my-cluster --region us-east-2
eksctl utils associate-iam-oidc-provider --region=us-east-2 --cluster=my-cluster --approve
eksctl create iamserviceaccount \
        --name ebs-csi-controller-sa \
        --namespace kube-system \
        --cluster my-cluster \
        --role-name AmazonEKS_EBS_CSI_DriverRole \
        --role-only \
        --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
        --approve
eksctl create addon --name aws-ebs-csi-driver --cluster my-cluster --region us-east-2 --force

aws eks update-kubeconfig --region us-east-2 --name my-cluster

kubectl get nodes -o wide

kubectl get pods -A -o wide

eksctl delete cluster --name my-cluster --region us-east-2

### Deploy
kubectl create namespace eks-todo-list-app
kubectl apply -f mongo-cloud.yaml -n eks-todo-list-app
kubectl apply -f app-cloud.yaml -n eks-todo-list-app

kubectl get pods -n eks-todo-list-app
kubectl get all -n eks-todo-list-app

(get IP)
kubectl get service flask-app -n eks-todo-list-app
(debug)
kubectl describe pod mongodb-6f84848985-9rmrb -n eks-todo-list-app
(delete all)
kubectl delete namespace eks-todo-list-app

a74b9445d3b374c0a9dfed61b1904d79-331530631.us-east-2.elb.amazonaws.com

(delete deployment)
kubectl delete deployment flask-app -n eks-todo-list-app


### ReplicationController
(Test Steps)
kubectl apply -f app-cloud.yaml -n eks-todo-list-app

kubectl get rc -n eks-todo-list-app


(Delete Steps)
kubectl get pods -l app=flask-app-rc -n eks-todo-list-app

kubectl delete pod flask-app-rc-9sr5w -n eks-todo-list-app

kubectl get pods -l app=flask-app-rc -n eks-todo-list-app -w

(delete rc)
kubectl delete rc flask-app-rc -n eks-todo-list-app

### Rolling Update
(Add RollingUpdate section)
kubectl apply -f app-cloud.yaml -n eks-todo-list-app

(Go to app)
cd ../app
docker build -t yuwei2002/flask-todo-app:v2 .
docker push yuwei2002/flask-todo-app:v2

(Update YAML)
kubectl apply -f app-cloud.yaml -n eks-todo-list-app
(Check rollout status)
kubectl rollout status deployment/flask-app -n eks-todo-list-app
kubectl get pods -n eks-todo-list-app -w

(check which images)
kubectl describe deployment flask-app -n eks-todo-list-app | grep -i image
(rollback)
kubectl rollout undo deployment/flask-app -n eks-todo-list-app


### 7
Update app.py

docker build -t yuwei2002/flask-todo-app:v3 .

docker push yuwei2002/flask-todo-app:v3

kubectl apply -f app-cloud.yaml -n eks-todo-list-app

kubectl get pods -n eks-todo-list-app



kubectl get service flask-app -n eks-todo-list-app

a83ce38b3065c4792891b4bcaf8c8ad4-118863242.us-east-2.elb.amazonaws.com

(wait 30s)
curl http://a83ce38b3065c4792891b4bcaf8c8ad4-118863242.us-east-2.elb.amazonaws.com/toggle-ready

curl http://a83ce38b3065c4792891b4bcaf8c8ad4-118863242.us-east-2.elb.amazonaws.com/toggle-health

kubectl describe pod flask-app-deployment-68d8f9f787-9d744 -n eks-todo-list-app

### Clearn UP
eksctl delete cluster --name my-cluster --region us-east-2