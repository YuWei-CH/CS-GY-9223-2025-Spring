# Cloud Computing Assignment2

### All commands below based on Ubuntu 22.04 LTS and AMD64 CPU

# **Part 1: Creating an Application:**

1. Get App from this link: https://drive.google.com/drive/u/0/folders/19AZciSY1l2neLVfJUzqRG4a_mDstnaK_
2. Install or start MongoDB
    
    ```bash
    # All the following commands will run at Linux
    sudo systemctl start mongod
    ```
    
    ```bash
    #or we can start with brew
    brew services start mongodb-community@6.0
    ```
    
3. Run the application 
    
    ```bash
    python3 app.py
    ```
    

Test the Todo List APP

# **Part 2: Containerizing the Application on Docker:**

1. Create a Dockerfile 

```bash
touch Dockerfile
```

1. Create an Dockerfile based on TA’s template (https://github.com/PrateekKumar1709/Docker-Demo/blob/main/cat-gif-app/single-container/Dockerfile)
    
    ```docker
    # Use an official Python runtime as the base image
    FROM python:3.9-slim
    
    # Set the working directory in the container
    WORKDIR /app
    
    # Copy the current directory contents into the container at /app
    COPY . /app
    
    # Upgrade pip and install the required packages
    RUN pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir -r requirements.txt
    
    # Make port 5050 available to the world outside this container
    EXPOSE 5050
    
    # Define environment variable
    ENV NAME="World"
    
    # Run app.py when the container launches
    CMD ["python", "app.py"]
    ```
    
2. Build Docker
    
    ```bash
    docker build -t flask-app .
    ```
    
    ![Screenshot 2025-03-12 at 9.33.34 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_9.33.34_PM.png)
    
3. Write a docker compose (ref: [https://hub.docker.com/_/mongo](https://hub.docker.com/_/mongo), https://github.com/docker/compose)
    
    ```yaml
    services:
      mongodb:
        image: "mongo:latest"
        ports:
          - "27017:27017"
        environment:
          - MONGO_INITDB_DATABASE=camp2016
        volumes:
          - mongo_data:/data/db
    
      flask_app:
        image: "flask-app:latest"  # Use pre-built image
        ports:
          - "5050:5050"
        depends_on:
          - mongodb
        environment:
          - MONGO_HOST=mongodb
          - MONGO_PORT=27017
    volumes:
      mongo_data:
    ```
    
4. Start  or stop services for the flask app and MongoDB container 
    
    ```bash
    docker compose up -d 
    
    docker compose down
    ```
    
    ![Screenshot 2025-03-12 at 9.36.21 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_9.36.21_PM.png)
    
    ![Screenshot 2025-03-12 at 9.36.55 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_9.36.55_PM.png)
    
5. Tag that Docker image 
    
    ```bash
    docker tag app-flask_app yuwei2002/flask-todo-app:latest
    ```
    
6. Push the Docker image to Dockerhub 
    
    ```bash
    docker push yuwei2002/flask-todo-app:latest
    ```
    
    ![Screenshot 2025-03-12 at 9.40.50 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_9.40.50_PM.png)
    
    ![Screenshot 2025-03-12 at 9.41.13 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_9.41.13_PM.png)
    

# **Part 3: Deploying the Application on Minikube:**

1. Start Minikube using the command-line interface: 
    
    ```bash
    minikube start
    ```
    
    ![Screenshot 2025-03-12 at 9.44.23 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_9.44.23_PM.png)
    
2. Create two pods: one for the flask app and one for the MongoDB to store
data. 
    
    ```yaml
    # Flask-app
    # Service
    apiVersion: v1
    kind: Service
    metadata:
      name: flask-app
    spec:
      selector:
        app: flask-app
      ports:
        - protocol: TCP
          port: 80
          targetPort: 5050
      type: LoadBalancer
    ---
    # Deployment
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: flask-app
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: flask-app
      template:
        metadata:
          labels:
            app: flask-app
        spec:
          containers:
            - name: flask-app
              image: yuwei2002/flask-todo-app:latest
              ports:
                - containerPort: 5050
              env:
                - name: MONGO_HOST
                  value: "mongodb"
                - name: MONGO_PORT
                  value: "27017"
              resources:
                requests:
                  cpu: "0.5"
                  memory: "512Mi"
                limits:
                  memory: "512Mi"
                  cpu: "1"
              imagePullPolicy: Always
    ```
    
    ```yaml
    # MongoDB
    # Persistent volume claim
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: mongo-pvc
    spec:
      accessModes:
        - ReadWriteOnce
      volumeMode: Filesystem
      storageClassName: standard # gp2 # AWS EBS storage
      resources:
        requests:
          storage: 1Gi
    ---
    # Service
    apiVersion: v1
    kind: Service
    metadata:
      name: mongodb
    spec:
      selector:
        app: mongodb
      ports:
        - port: 27017
          targetPort: 27017
    ---
    # Deployment
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: mongodb
    spec:
      selector:
        matchLabels:
          app: mongodb
      template:
        metadata:
          labels:
            app: mongodb
        spec:
          containers:
            - name: mongodb
              image: mongo:latest
              ports:
                - containerPort: 27017
              env:
                - name: MONGO_INITDB_DATABASE
                  value: camp2016
              volumeMounts:
                - name: mongo-data
                  mountPath: /data/db
              resources:
                requests:
                  cpu: "0.3"
                  memory: "512Mi"
                limits:
                  memory: "512Mi"
                  cpu: "0.5"
          volumes:
            - name: mongo-data
              persistentVolumeClaim:
                claimName: mongo-pvc
    
    ```
    
3. Apply these YAML using  `kubectl`
    
    ```bash
    kubectl apply -f app-cloud.yaml
    kubectl apply -f mongo-cloud.yaml
    ```
    
    ![Screenshot 2025-03-12 at 10.14.00 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_10.14.00_PM.png)
    
4. Test the application 
    
    ```bash
    # Port Forwarding
    kubectl port-forward service/flask-app 8080:80 -n default
    ```
    
    ![Screenshot 2025-03-12 at 10.15.58 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_10.15.58_PM.png)
    
5. Cleanup and stop 
    
    ```bash
    kubectl delete deployments --all
    minikube stop
    ```
    

### **Part 4: Deploying the Application on AWS EKS:**

Ref: https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html

1. Install AWS CLI 
    
    ```bash
    # Linux
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    
    #MacOS
    brew install weaveworks/tap/eksctl
    brew install awscli
    ```
    
2. Create credential file for cluster 
    
    ```bash
    aws configure
    # Check identity
    aws sts get-caller-identity
    ```
    
3. Setup eksctl 
    
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
    
4. Create an AWS EKS cluster  with an IAM using eksctl
    
    ```bash
    # Create cluster
    eksctl create cluster --name my-cluster --region us-east-2
    
    # created IAM Open ID Connect provider
    eksctl utils associate-iam-oidc-provider --region=us-east-2 --cluster=my-cluster --approve
    # Create IAM
    eksctl create iamserviceaccount \
            --name ebs-csi-controller-sa \
            --namespace kube-system \
            --cluster my-cluster \
            --role-name AmazonEKS_EBS_CSI_DriverRole \
            --role-only \
            --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
            --approve
    ```
    
5. Install `aws-ebs-csi-driver` since we using AWS EBS storage 
    
    ```bash
    eksctl create addon --name aws-ebs-csi-driver --cluster my-cluster --region us-east-2 --force
    ```
    
6. Configure the Kubernetes CLI (kubectl) to connect to the EKS cluster 
    
    ```bash
    Configure the Kubernetes CLI (kubectl) to connect to the EKS cluster
    ```
    
    Check connection 
    
    ```bash
    kubectl get nodes -o wide
    ```
    
    ![Screenshot 2025-03-12 at 10.32.48 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_10.32.48_PM.png)
    
7. Deployment (based on previous YAML in Part 3) 
    
    Step 1: Change the `storageClassName` in mongo-cloud.yaml from **standard** to **gp2** since we want to use the AWS EBS storage
    
    Step 2: Create a namespace for management 
    
    ```bash
    kubectl create namespace eks-todo-list-app
    ```
    
    Step 3: Apply yaml
    
    ```bash
    kubectl apply -f mongo-cloud.yaml -n eks-todo-list-app
    kubectl apply -f app-cloud.yaml -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-12 at 10.39.21 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_10.39.21_PM.png)
    
    Check If successful:
    
    ```bash
    kubectl get pods -n eks-todo-list-app
    kubectl get all -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-12 at 10.40.20 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_10.40.20_PM.png)
    
8. Test the application 
    
    ```bash
    kubectl get service flask-app -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-12 at 10.41.56 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_10.41.56_PM.png)
    
    ![Screenshot 2025-03-12 at 10.42.33 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_10.42.33_PM.png)
    

# **Part 5: Replication controller feature:**

1. Create an app-cloud.yaml to use ReplicationController instead of Deployment 
    
    ```yaml
    # ReplicationController
    apiVersion: v1
    kind: ReplicationController
    metadata:
      name: flask-app-rc
      namespace: eks-todo-list-app
    spec:
      replicas: 5
      selector:
        app: flask-app-rc
      template:
        metadata:
          labels:
            app: flask-app-rc
        spec:
          containers:
            - name: flask-app
              image: yuwei2002/flask-todo-app:latest
              ports:
                - containerPort: 5050
              env:
                - name: MONGO_HOST
                  value: "mongodb"
                - name: MONGO_PORT
                  value: "27017"
              resources:
                requests:
                  cpu: "0.3"
                  memory: "256Mi"
                limits:
                  cpu: "0.5"
                  memory: "512Mi"
    ```
    
2. Create the replication controller :
    
    ```bash
    kubectl apply -f app-rc.yaml -n eks-todo-list-app
    ```
    
    verify that the specified number of replicas are created and running 
    
    ```bash
    kubectl get rc -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-13 at 3.46.57 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_3.46.57_PM.png)
    
3. Test the replication controller:
    
    Step 1: Get pods name 
    
    ```bash
    kubectl get pods -l app=flask-app-rc -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-13 at 3.50.42 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_3.50.42_PM.png)
    
    Step 2: Delete a pod (flask-app-rc-52tzx)
    
    ```bash
    kubectl delete pod flask-app-rc-8bkwm -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-13 at 3.51.16 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_3.51.16_PM.png)
    
    Step 3: Watch if a new pod auto running: 
    
    ```bash
    kubectl get pods -l app=flask-app-rc -n eks-todo-list-app -w
    ```
    
    ![Screenshot 2025-03-13 at 3.51.37 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_3.51.37_PM.png)
    
4. Update number of replicas and verify
    
    Step 1: Change `replicas` from **5** to **3**
    
    Step 2: Apply YAML: 
    
    ```bash
    kubectl apply -f app-rc.yaml -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-13 at 3.53.13 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_3.53.13_PM.png)
    
    Step 3: Verify: 
    
    ```bash
    kubectl get rc -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-13 at 3.53.32 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_3.53.32_PM.png)
    

# **Part 6: Rolling update strategy:**

1. Since replication controller do not suppport update strategy, we need back to Deployment 
    
    ```yaml
    # Flask-app
    # Service
    apiVersion: v1
    kind: Service
    metadata:
      name: flask-app
    spec:
      selector:
        app: flask-app-rc
      ports:
        - protocol: TCP
          port: 80
          targetPort: 5050
      type: LoadBalancer
    ---
    # Deployment
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: flask-app-deployment
      namespace: eks-todo-list-app
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: flask-app-rc
      strategy:
        type: RollingUpdate
        rollingUpdate:
          maxSurge: 1
          maxUnavailable: 1
      template:
        metadata:
          labels:
            app: flask-app-rc
        spec:
          containers:
            - name: flask-app
              image: yuwei2002/flask-todo-app:v2 # latest
              ports:
                - containerPort: 5050
              env:
                - name: MONGO_HOST
                  value: "mongodb"
                - name: MONGO_PORT
                  value: "27017"
              resources:
                requests:
                  cpu: "0.3"
                  memory: "256Mi"
                limits:
                  cpu: "0.5"
                  memory: "512Mi"
    ```
    
2. Apply YAML 
    
    ```bash
    kubectl apply -f app-cloud.yaml -n eks-todo-list-app
    ```
    
3. Update the Docker image for the deployment to a new version 
    
    ```bash
    docker build -t yuwei2002/flask-todo-app:v2 .
    docker push yuwei2002/flask-todo-app:v2
    ```
    
    ![Screenshot 2025-03-12 at 11.27.25 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_11.27.25_PM.png)
    
4. Update YAML to use new docker: Change tag in image
5. Apply YAML  
    
    ```bash
    kubectl apply -f kube/app-cloud.yaml -n eks-todo-list-app
    ```
    
6. Monitor the rolling update progress
    
    ```bash
    kubectl rollout status deployment/flask-app-deployment -n eks-todo-list-app
    # Watch pods being updated
    kubectl get pods -n eks-todo-list-app -l app=flask-app-rc -w
    ```
    
    ![Screenshot 2025-03-12 at 11.32.37 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_11.32.37_PM.png)
    
7. Test the appliction: 
    
    ```bash
    kubectl get service flask-app -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-12 at 11.37.08 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_11.37.08_PM.png)
    
    ![Screenshot 2025-03-12 at 11.36.49 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_11.36.49_PM.png)
    
8. Ensure application using New Docker image version
    
    ![Screenshot 2025-03-12 at 11.34.30 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-12_at_11.34.30_PM.png)
    

# **Part 7: Health monitoring:**

1. Add health and ready for probe in [app.py](http://app.py/) 
    
    ```python
    from flask import Flask, render_template,request,redirect,url_for # For flask implementation
    from pymongo import MongoClient # Database connector
    from bson.objectid import ObjectId # For ObjectId to work
    from bson.errors import InvalidId # For catching InvalidId exception for ObjectId
    import os
    import threading # Add threading for timer functionality
    
    mongodb_host = os.environ.get('MONGO_HOST', 'localhost')
    mongodb_port = int(os.environ.get('MONGO_PORT', '27017'))
    client = MongoClient(mongodb_host, mongodb_port)    #Configure the connection to the database
    db = client.camp2016    #Select the database
    todos = db.todo #Select the collection
    
    app = Flask(__name__)
    title = "TODO with Flask(V2)"
    heading = "ToDo Reminder"
    #modify=ObjectId()
    
    # Global variables to control health and readiness status
    app_healthy = True
    app_ready = True
    ready_timer = None # Timer to track auto-reset
    
    def redirect_url():
    	return request.args.get('next') or \
    		request.referrer or \
    		url_for('index')
    
    @app.route("/list")
    def lists ():
    	#Display the all Tasks
    	todos_l = todos.find()
    	a1="active"
    	return render_template('index.html',a1=a1,todos=todos_l,t=title,h=heading)
    
    @app.route("/")
    @app.route("/uncompleted")
    def tasks ():
    	#Display the Uncompleted Tasks
    	todos_l = todos.find({"done":"no"})
    	a2="active"
    	return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading)
    
    @app.route("/completed")
    def completed ():
    	#Display the Completed Tasks
    	todos_l = todos.find({"done":"yes"})
    	a3="active"
    	return render_template('index.html',a3=a3,todos=todos_l,t=title,h=heading)
    
    @app.route("/done")
    def done ():
    	#Done-or-not ICON
    	id=request.values.get("_id")
    	task=todos.find({"_id":ObjectId(id)})
    	if(task[0]["done"]=="yes"):
    		todos.update_one({"_id":ObjectId(id)}, {"$set": {"done":"no"}})
    	else:
    		todos.update_one({"_id":ObjectId(id)}, {"$set": {"done":"yes"}})
    	redir=redirect_url()	# Re-directed URL i.e. PREVIOUS URL from where it came into this one
    
    #	if(str(redir)=="http://localhost:5000/search"):
    #		redir+="?key="+id+"&refer="+refer
    
    	return redirect(redir)
    
    #@app.route("/add")
    #def add():
    #	return render_template('add.html',h=heading,t=title)
    
    @app.route("/action", methods=['POST'])
    def action ():
    	#Adding a Task
    	name=request.values.get("name")
    	desc=request.values.get("desc")
    	date=request.values.get("date")
    	pr=request.values.get("pr")
    	todos.insert_one({ "name":name, "desc":desc, "date":date, "pr":pr, "done":"no"})
    	return redirect("/list")
    
    @app.route("/remove")
    def remove ():
    	#Deleting a Task with various references
    	key=request.values.get("_id")
    	todos.delete_one({"_id":ObjectId(key)})
    	return redirect("/")
    
    @app.route("/update")
    def update ():
    	id=request.values.get("_id")
    	task=todos.find({"_id":ObjectId(id)})
    	return render_template('update.html',tasks=task,h=heading,t=title)
    
    @app.route("/action3", methods=['POST'])
    def action3 ():
    	#Updating a Task with various references
    	name=request.values.get("name")
    	desc=request.values.get("desc")
    	date=request.values.get("date")
    	pr=request.values.get("pr")
    	id=request.values.get("_id")
    	todos.update_one({"_id":ObjectId(id)}, {'$set':{ "name":name, "desc":desc, "date":date, "pr":pr }})
    	return redirect("/")
    
    @app.route("/search", methods=['GET'])
    def search():
    	#Searching a Task with various references
    
    	key=request.values.get("key")
    	refer=request.values.get("refer")
    	if(refer=="id"):
    		try:
    			todos_l = todos.find({refer:ObjectId(key)})
    			if not todos_l:
    				return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading,error="No such ObjectId is present")
    		except InvalidId as err:
    			pass
    			return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading,error="Invalid ObjectId format given")
    	else:
    		todos_l = todos.find({refer:key})
    	return render_template('searchlist.html',todos=todos_l,t=title,h=heading)
    
    @app.route("/about")
    def about():
    	return render_template('credits.html',t=title,h=heading)
    
    # livenessProbe
    @app.route("/health")
    def health():
        if app_healthy:
            return {"status": "healthy"}, 200
        else:
            return {"status": "unhealthy"}, 500
    # readinessProbe
    @app.route("/ready")
    def ready():
        if not app_ready:
            return {"status": "not ready", "error": "Readiness manually disabled"}, 503
        try:
            client.server_info() # Check if MongoDB connection is still alive
            return {"status": "ready"}, 200
        except Exception as e:
            return {"status": "not ready", "error": str(e)}, 503
    
    # reset timer for /ready
    def reset_ready():
        global app_ready, ready_timer
        app_ready = True
        ready_timer = None
        print("Readiness automatically reset to True after 30 seconds")
    
    # Test endpoints to simulate failures
    @app.route("/toggle-health")
    def toggle_health():
        global app_healthy
        app_healthy = not app_healthy
        status = "unhealthy" if not app_healthy else "healthy"
        return {"message": f"Health status toggled to {status}"}, 200
    
    # Test endpoint to toggle readiness status
    @app.route("/toggle-ready")
    def toggle_ready():
        global app_ready, ready_timer
        app_ready = not app_ready
        status = "not ready" if not app_ready else "ready"
        # If toggled to not ready, set timer to reset after 30 seconds
        if not app_ready:
            if ready_timer:
                ready_timer.cancel()
            ready_timer = threading.Timer(30.0, reset_ready)
            ready_timer.daemon = True  # Make thread daemon so it won't block app shutdown
            ready_timer.start()
            return {"message": f"Readiness status toggled to {status}. Will reset in 30 seconds."}, 200
        else:
            if ready_timer:
                ready_timer.cancel()
                ready_timer = None
            return {"message": f"Readiness status toggled to {status}"}, 200
    
    if __name__ == "__main__":
    	env = os.environ.get('FLASK_ENV', 'development')
    	port = int(os.environ.get('PORT', 5050))
    	debug = False if env == 'production' else True
    	app.run(host='0.0.0.0', port=port, debug=debug)
    	# Careful with the debug mode..
    ```
    
2. Build a new docker for app.py and push to Dockerhub 
    
    ```yaml
    docker build -t yuwei2002/flask-todo-app:v3 .
    docker push yuwei2002/flask-todo-app:v3
    ```
    
    ![Screenshot 2025-03-13 at 4.10.06 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_4.10.06_PM.png)
    
    ![Screenshot 2025-03-13 at 4.10.57 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_4.10.57_PM.png)
    
    ![Screenshot 2025-03-13 at 4.11.15 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-13_at_4.11.15_PM.png)
    
3. Add livenessProbe and readinessProbe to app-cloud.yaml 
    
    ```yaml
    # Flask-app
    # Service
    apiVersion: v1
    kind: Service
    metadata:
      name: flask-app
    spec:
      selector:
        app: flask-app-rc
      ports:
        - protocol: TCP
          port: 80
          targetPort: 5050
      type: LoadBalancer
    ---
    # Deployment
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: flask-app-deployment
      namespace: eks-todo-list-app
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: flask-app-rc
      strategy:
        type: RollingUpdate
        rollingUpdate:
          maxSurge: 1
          maxUnavailable: 1
      template:
        metadata:
          labels:
            app: flask-app-rc
        spec:
          containers:
            - name: flask-app
              image: yuwei2002/flask-todo-app:v3 # latest
              ports:
                - containerPort: 5050
              env:
                - name: MONGO_HOST
                  value: "mongodb"
                - name: MONGO_PORT
                  value: "27017"
              resources:
                requests:
                  cpu: "0.3"
                  memory: "256Mi"
                limits:
                  cpu: "0.5"
                  memory: "512Mi"
              imagePullPolicy: Always
              livenessProbe: # Http Liveness Probe
                httpGet:
                  path: /health
                  port: 5050
                initialDelaySeconds: 30
                periodSeconds: 10
                timeoutSeconds: 5
                failureThreshold: 3
              readinessProbe: # Http Readiness Probe
                httpGet:
                  path: /ready
                  port: 5050
                initialDelaySeconds: 15
                periodSeconds: 5
                timeoutSeconds: 3
                successThreshold: 1
                failureThreshold: 3
    ```
    
4. Apply the updated YAML TODO
    
    ```bash
    kubectl apply -f app-cloud-copy.yaml -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-14 at 11.05.41 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-14_at_11.05.41_PM.png)
    
5. Get external IP of deployment 
    
    ```bash
    kubectl get service flask-app -n eks-todo-list-app
    
    # a178b2df693a147af84fb7579c29c31a-115792124.us-east-2.elb.amazonaws.com
    ```
    
    ![Screenshot 2025-03-14 at 11.07.22 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-14_at_11.07.22_PM.png)
    
6. Monitor health of a pod (using pod name) 
    
    ```bash
    kubectl describe pod flask-app-deployment-68d8f9f787-9d744 -n eks-todo-list-app
    ```
    
    ![Screenshot 2025-03-14 at 11.18.08 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-14_at_11.18.08_PM.png)
    
7. Trigger an active readiness prob via `curl` 
    
    ```bash
    curl http://a178b2df693a147af84fb7579c29c31a-115792124.us-east-2.elb.amazonaws.com/toggle-ready
    ```
    
    ![Screenshot 2025-03-14 at 11.09.15 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-14_at_11.09.15_PM.png)
    
    To better test the liveness prob, we set the duration of “not ready” to 30s.
    
    ![Screenshot 2025-03-14 at 11.09.26 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-14_at_11.09.26_PM.png)
    
8. Trigger an active readiness prob via `curl` 
    
    ```bash
    curl http://a178b2df693a147af84fb7579c29c31a-115792124.us-east-2.elb.amazonaws.com/toggle-health
    ```
    
    ![Screenshot 2025-03-14 at 11.13.20 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-14_at_11.13.20_PM.png)
    
    Once liveness prob detect failure, it will restart the pod.
    
    ![Screenshot 2025-03-14 at 11.13.45 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-14_at_11.13.45_PM.png)
    
    Result of health monitor:
    
    ![Screenshot 2025-03-14 at 11.19.02 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-14_at_11.19.02_PM.png)
    

### Step 8: Alerting:

1. Install Prometheus 
    
    ```bash
    wget https://github.com/prometheus/prometheus/releases/download/v3.2.1/prometheus-3.2.1.linux-amd64.tar.gz
    
    tar xvfz prometheus-*.tar.gz
    
    cd prometheus-3.2.1.linux-amd64/
    ```
    
2. Configure Prometheus 
    
    Step 1: modify prometheus.yml
    
    ```yaml
    global:
      scrape_interval: 15s # collect metrics from targets every 15 seconds
      evaluation_interval: 15s
    
    rule_files:
      - "probe-alerts.yml"
    
    alerting:
      alertmanagers:
        - static_configs:
            - targets:
                - alertmanager:9093
    
    scrape_configs:
      - job_name: "all-kubernetes-pods"
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          # Add namespace as a label
          - source_labels: [__meta_kubernetes_namespace]
            action: replace
            target_label: kubernetes_namespace
          # Add pod name as a label
          - source_labels: [__meta_kubernetes_pod_name]
            action: replace
            target_label: kubernetes_pod_name
    
      # Uses direct HTTP checks instead
      - job_name: "blackbox"
        metrics_path: /metrics
        static_configs:
          - targets:
              - localhost:9115
    
      # Direct health check
      - job_name: "app-health-check"
        metrics_path: /health
        scrape_interval: 10s
        static_configs:
          - targets:
              - a178b2df693a147af84fb7579c29c31a-115792124.us-east-2.elb.amazonaws.com
        relabel_configs:
          - source_labels: [__address__]
            target_label: instance
          - target_label: __address__
            replacement: a178b2df693a147af84fb7579c29c31a-115792124.us-east-2.elb.amazonaws.com:80
    
    ```
    
    step 2: Create probe-alerts.yml 
    
    ```bash
    touch probe-alerts.yml
    ```
    
    ```yaml
    groups:
      - name: probe-alerts
        rules:
          - alert: ProbeFailureThresholdExceeded
            expr: probe_success == 0
            for: 45s
            labels:
              severity: critical
            annotations:
              summary: "Probe failure detected"
              description: "Probe {{ $labels.instance }} has been failing for 45 seconds, which may trigger Kubernetes restarts."
    
          - alert: HighProbeFailureRate
            expr: sum(rate(probe_success{job="blackbox"}[5m]) == 0) / sum(rate(probe_success{job="blackbox"}[5m])) > 0.1
            for: 45s
            labels:
              severity: warning
            annotations:
              summary: "High probe failure rate detected"
              description: "More than 10% of probes are failing in the last 10 minutes."
    
          - alert: SlowResponseTime
            expr: probe_duration_seconds > 1
            for: 45s
            labels:
              severity: warning
            annotations:
              summary: "Slow probe response time"
              description: "Probe {{ $labels.instance }} response time is above 1 second for more than 5 minutes."
    
    ```
    
3. Create a webhooks 
    
    Step 1: Following [https://api.slack.com/messaging/webhooks](https://api.slack.com/messaging/webhooks) to create a webhooks
    
    Step 2: Test if success
    
    ```bash
    curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/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
    ```
    
4. Install Alertmanager 
    
    ```bash
    wget https://github.com/prometheus/alertmanager/releases/download/v0.28.1/alertmanager-0.28.1.linux-amd64.tar.gz
    
    tar xvfz alertmanager-*.tar.gz
    
    cd alertmanager-0.28.1.linux-amd64/
    ```
    
5. Configure Alertmanager 
    
    Step 1: Modify alertmanager.yml 
    
    ```yaml
    global:
      resolve_timeout: 1m # Faster resolution notifications
      slack_api_url: "https://hooks.slack.com/services/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"
    
    route:
      group_by: ["alertname", "job"]
      group_wait: 10s
      group_interval: 45s
      repeat_interval: 4h
      receiver: "slack-notifications"
    
    receivers:
      - name: "slack-notifications"
        slack_configs:
          - channel: "#alerts"
            send_resolved: true
            title: "{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}"
            text: "{{ range .Alerts }}{{ .Annotations.description }}\n{{ end }}"
            color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'
    ```
    
6. Testing the Alerting System
    
    Step 1:  Start alertmanager
    
    ```bash
    ./alertmanager --config.file=alertmanager.yml &
    ```
    
    ![Screenshot 2025-03-15 at 11.46.37 AM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-15_at_11.46.37_AM.png)
    
    Step 2: Start prometheus 
    
    ```bash
    cd ../prometheus-3.2.1.linux-amd64/
    
    ./prometheus --config.file=prometheus.yml &
    ```
    
    ![Screenshot 2025-03-15 at 11.47.11 AM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-15_at_11.47.11_AM.png)
    
    ![Screenshot 2025-03-15 at 11.47.22 AM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-15_at_11.47.22_AM.png)
    
    Step 3: Trigger failure 
    
    ```bash
    curl http://a178b2df693a147af84fb7579c29c31a-115792124.us-east-2.elb.amazonaws.com/toggle-health
    ```
    
    ![Screenshot 2025-03-15 at 11.57.53 AM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-15_at_11.57.53_AM.png)
    
    Step 4: Watch firing: 
    
    Open the webui ([http://localhost:9090](http://localhost:9090/))
    
    ![Screenshot 2025-03-15 at 11.54.13 AM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-15_at_11.54.13_AM.png)
    
    Slack Update:
    
    ![Screenshot 2025-03-15 at 12.23.58 PM.png](Cloud%20Computing%20Assignment2%201b5036418ff680baba50da55f1a8a305/Screenshot_2025-03-15_at_12.23.58_PM.png)