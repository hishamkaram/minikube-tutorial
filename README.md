# How to Deploy a Simple Django on minikube (local)

This article focuses on implementing the kubernetes hello-minikube tutorial adapted to a conventional Django application. The codebase for this tutorial can be cloned from [my github repo](https://github.com/hishamkaram/minikube-tutorial).

- requirements:
    - OS:

        - Mac OS System / Linux
        - this tutorial uses macOS Big Sur version: `v11.3.1`
    - minikube:

        - Minikube is one of the easiest ways to run a single node Kubernetes cluster locally. you can install it from [here](https://minikube.sigs.k8s.io/docs/start/)
        - version: `v1.20.0`
    - Docker:

        - Docker is a set of platform as a service products that use OS-level virtualization to deliver software in packages called containers. you can install it from [here](https://www.docker.com/products/docker-desktop)
        - version `v20.10.6`
    - Kubectl
    
        - The Kubernetes command line tool is called kubectl and is used to deploy and manage applications. This is done by creating, updating and deleting components as well as inspecting cluster resources, you can install it from [here](https://kubernetes.io/docs/tasks/tools/)


## 1. Project Source Code:
In order to get the best of this tutorial, the project github repo should be cloned:
```
$ git clone https://github.com/hishamkaram/minikube-tutorial.git
```
## 2. Minikube
To start the Kubernetes cluster using minikube, run the command:
```shell
$ minikube start
😄  minikube v1.20.0 on Darwin 11.3.1 (arm64)
✨  Automatically selected the docker driver
👍  Starting control plane node minikube in cluster minikube
🚜  Pulling base image ...
💾  Downloading Kubernetes v1.20.2 preload ...
    > preloaded-images-k8s-v10-v1...: 514.95 MiB / 514.95 MiB  100.00% 6.07 MiB
    > gcr.io/k8s-minikube/kicbase...: 324.66 MiB / 324.66 MiB  100.00% 2.74 MiB
    > gcr.io/k8s-minikube/kicbase...: 324.66 MiB / 324.66 MiB  100.00% 5.05 MiB
🔥  Creating docker container (CPUs=2, Memory=3885MB) ...
🐳  Preparing Kubernetes v1.20.2 on Docker 20.10.6 ...
    ▪ Generating certificates and keys ...
    ▪ Booting up control plane ...
    ▪ Configuring RBAC rules ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

 - this command will run several processes including:
    - The creation and configuration of a Virtual Machine which runs a single-node cluster.
    
    - Setting the default kubectl context to minikube.
- The status of the minikube cluster can be determined by running the following command:
    ```shell
    $ minikube status
    minikube
    type: Control Plane
    host: Running
    kubelet: Running
    apiserver: Running
    kubeconfig: Configured
    ```
- The docker command line in the host machine can be configured to utilize the docker daemon within minikube by running:
    ```shell
    $ eval $(minikube docker-env)
    ```
- There are many management commands that are used by kubectl to view the state of the Kubernetes cluster. Fortunately, minikube provides a dashboard so we don’t have to worry about all the explicit commands. To view the dashboard, run the command:
    ````shell
    $ minikube dashboard
    ````

This opens the default browser and displays the current state of the Kubernetes cluster.

## 3. Docker
As Kubernetes expects a containerized application, we will be using docker to get started. It’s assumed docker has already been installed and we are using the minikube docker daemon.

- The following Dockerfile is in the root directory under this path `./docker/Dockerfile`:
```docker
FROM python:3.9.2-slim-buster
LABEL maintainer="AnyManager Dev Team<dev@anymanager.io>"

# environment variables
ENV DEBCONF_NOWARNINGS yes
ENV USER_NAME appuser
ENV APP_DIR app
ENV FULL_DIR /home/${USER_NAME}/${APP_DIR}
ENV PORT 8080
ENV USER_UID 1010
ENV GROUP_GID 1010
ENV SYSTEM_VERSION_COMPAT 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PIP_NO_CACHE_DIR 1
ENV PYTHONUNBUFFERED 1

# create non root user
RUN groupadd -g ${USER_UID} ${USER_NAME} && useradd -u ${GROUP_GID} -m -g ${USER_NAME} ${USER_NAME} && mkdir -p ${FULL_DIR}

# change the current path in the contianer
WORKDIR ${FULL_DIR}
COPY requirements.txt requirements.txt
# install python libraries
RUN pip install -r requirements.txt

COPY . .

RUN chown -R ${USER_NAME}:${USER_NAME} ${FULL_DIR} && \
    find ${FULL_DIR} -type f -exec chmod 644 {} \; && \
    find ${FULL_DIR} -type d -exec chmod 755 {} \; && \
    chgrp -R ${USER_NAME} ${FULL_DIR}

# cleanup image
RUN rm -rf ~/.cache/pip && rm -rf /root/.cache
RUN apt autoremove --purge -y && apt autoclean -y && apt-get clean -y
RUN rm -rf /var/lib/apt/lists/* && apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN echo "Yes, do as I say!" | apt-get remove --force-yes login && \
    dpkg --remove --force-depends wget
USER ${USER_NAME}

CMD python manage.py runserver 0.0.0.0:${PORT}
```
- The Dockerfile first defines the base image to build from, where in this case it’s the python:3.9.2-slim-buster image.
- The `LABEL` instruction is then used to add metadata to the image. This is the recommended way to specify the package maintainer as the MAINTAINER instruction has been deprecated.
- The ENV <VARIABLE> <var> directive sets the project root environmental variable, where the variable can be reused in several places as $<VARIABLE>. This allows for one point of modification in case some arbitrary variable needs to be changed.

- we create a non root user for some security reasons using:
    ```docker
    RUN groupadd -g ${USER_UID} ${USER_NAME} && useradd -u ${GROUP_GID} -m -g ${USER_NAME} ${USER_NAME} && mkdir -p ${FULL_DIR}
    ```

- The current working directory is then set using the WORKDIR instruction. The instruction resolves the `$FULL_DIR` environmental variable previously set. The working directory will be the execution context of any subsequent RUN, COPY, ENTRYPOINT or CMD instructions, unless explicitly stated.

- The `COPY` instruction is then used to copy the requirements.txt file from the current directory of the local file system and adds them to the file system of the container. Copying the individual file ensures that the `RUN` pip install instruction’s build cache is only invalidated (forcing the step to be re-run) if specifically the requirements.txt file changes, leading to an efficient build process. See [the docker documentation](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/) for further details. It’s worth noting the `COPY` as opposed to the `ADD` instruction is the recommended command for copying files from the local file system to the container file system.

- install project requirements using:
    ```docker
    RUN pip install -r requirements.txt
    ```
- The rest of the project files are then copied into the container file system. This should be one of the last steps as the files are constantly changing leading to more frequent cache invalidations resulting in more frequent image builds.

- change the project files permission and ownership to non root user which we created before with this instruction:
    ```docker
    RUN chown -R ${USER_NAME}:${USER_NAME} ${FULL_DIR} && \
        find ${FULL_DIR} -type f -exec chmod 644 {} \; && \
        find ${FULL_DIR} -type d -exec chmod 755 {} \; && \
        chgrp -R ${USER_NAME} ${FULL_DIR}
    ```
    - please check [this tutorials](https://www.linux.com/training-tutorials/understanding-linux-file-permissions/) for more details about file permissions 
- minimise the amount of data stored in that particular docker layer by removing cache and apt cache using:
    ```docker
    RUN rm -rf ~/.cache/pip && rm -rf /root/.cache
    RUN apt autoremove --purge -y && apt autoclean -y && apt-get clean -y
    RUN rm -rf /var/lib/apt/lists/* && apt-get clean -y && \
        rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
    ```

- The final instruction executed is `CMD` which provides defaults for an executing container. In this case the default is to start the python web server.


### Building Docker
use the following command format to build the required docker image based on the Dockerfile:

```shell
$ docker build -f docker/Dockerfile -t <IMAGE_NAME>:<TAG> .
```
The `:<TAG>` parameter though optional, is recommended in order to keep track of the version of the docker image to be run e.g. `docker build -f docker/Dockerfile -t minikube-tutorial/mysite:v1.0 .` . The <IMAGE_NAME> can be any arbitrary string, but the recommended format is <REPO_NAME>/<APP_NAME> .

In order to list the built image within the minikube docker environment, run:

```shell
$ docker images
minikube-tutorial/mysite           v1.0      bd269e74149e   3 seconds ago   148MB
```

# 4. Deployment
Kubernetes uses the concept of [pods](https://kubernetes.io/docs/concepts/workloads/pods/) to run applications. There are different controllers used to manage the lifecycle of pods in a Kubernetes cluster. However, a `Deployment` controller forms one of easiest ways to create, update and delete pods in the cluster.

- Kubernetes commands can be executed by an [imperative](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/imperative-command/) or [declarative](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/) approach.
    
    - Imperative commands specify how an operation needs to be performed:
        > "Imperative" is a command - like "kubectl create service nodeport <myservicename>".
    
    - declarative approach is done by using configuration files which can be stored in version control. The preferred method is the declarative approach as the steps can be tracked and audited.

we will use declarative approach.

## Creating a Deployment 
we can find in kubernetes [docs](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#creating-a-deployment) an example of a Deployment. It creates a ReplicaSet to bring up three nginx Pods, let check out our deployment yaml for webserver which can be found user this path `k8s/web-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-app
  labels:
    app: django-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: django-app
  template:
    metadata:
      labels:
        app: django-app
    spec:
      containers:
        - name: django-app
          image: minikube-tutorial/mysite:v1.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          env:
            - name: POD_IP
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
            - name: HOST_IP
              valueFrom:
                fieldRef:
                  fieldPath: status.hostIP
```
From the spec file:
- The `metadata: name` field describes the deployment name, whereas the `metadata: labels` describes the labels for the deployment i.e. can be thought of as a tagging mechanism.
- The `spec: replicas` field defines the number of pods to run.
- The `spec: selector:` matchLabels field describes what pods the deployment should apply to.
- The `spec: template: metadata:` labels field indicates what labels should be assigned to the running pod. This label is what is found by the matchLabels field in the deployment.
- The `spec: template: spec` field, contains a list of `containers` that belong to this pod. In this case it indicates the pod has one container as it only has one image and name in the list.
- The deployment exposes port `8000` within the pod as defined in the `spec: template: spec: containers: ports` field.
- there are too many different ways to pass envriment variables to your container but right now, we are using the simplest way because we do not have secrets, please check the [docs](https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/).

let's create our deployment using the following command:
```shell
$ kubectl apply -f k8s/deployment.yaml
```
let's check if the deployment is created or not using the following command:
```shell
$ kubectl get deployments
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
django-app   1/1     1            1           17m
```
we can check the created [pods](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) using:
```shell
$ kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
django-app-55c6fbcffd-dvc7t   1/1     Running   0          17m
```
we can ssh into the django-app container using the following command:
```shell
$ kubectl exec -it <pod_name> <container_name> -- /bin/bash
```
- in our case pod name is `django-app-55c6fbcffd-dvc7t`
- in our case container name is: `django-app`

if you can see this `appuser@django-app-55c6fbcffd-dvc7t:~/app$ ` in your terminal, you already in the `django-app` container then migrating the database using `python manage.py migrate`

# 5. Services
When a deployment is created, each pod in the deployment has a unique IP address within the cluster. However, we need some kind of mechanism to allow the access of the pod IP address from outside the cluster. This is done by [Services](https://kubernetes.io/docs/concepts/services-networking/service/):
> An abstract way to expose an application running on a set of Pods as a network service.

## creating service
let's create a [NodePort service](https://kubernetes.io/docs/concepts/services-networking/service/#nodeport) to expose our deployment, let check the specs file (yaml file):
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  namespace: default
spec:
  ports:
    - port: 8080
      protocol: TCP
      targetPort: 8080
  selector:
    app: django-app
  type: NodePort

```
- The `metadata: name` field describes the name of the Service object that will be created and can be identified by running `kubectl get svc`.
- The `spec: selector` field specifies the <pod_label> and <pod_value> that the service applies to. This means that any pod matching <pod_key>=<pod_value> label will be exposed by the service, in our case `pod_key` is `app` and `pod_value` is `django-app`
- The `spec: ports` contains a yaml array. The protocol in the first item in the array is TCP where the pod `port: 8000` field is exposed to the Kubernetes cluster i.e. the cluster interacts with the pod on port `8000`. The `targetPort` is the port within the pod that it’s exposed through. If port is not defined, it will default to the `targetPort` . The `NodePort` type instructs the service to expose the pod to the node/host machine on a random port in the default range `30000–32767` , however an explicit nodePort can be set in the protocols array to specify which port in the default range the host machine can communicate with the pod .

let's create our service using:
```shell
$ kubectl get svc                            
NAME          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
kubernetes    ClusterIP   10.96.0.1       <none>        443/TCP          3h11m
web-service   NodePort    10.98.162.251   <none>        8080:30886/TCP   3m47s
```
let's access our webservice using:
```shell
minikube service --url <service_name>
🏃  Starting tunnel for service web-service.
|-----------|-------------|-------------|------------------------|
| NAMESPACE |    NAME     | TARGET PORT |          URL           |
|-----------|-------------|-------------|------------------------|
| default   | web-service |             | http://127.0.0.1:59423 |
|-----------|-------------|-------------|------------------------|
http://127.0.0.1:59423
❗  Because you are using a Docker driver on darwin, the terminal needs to be open to run it.
```
- in our case service name is: `web-service`
- open your browser and enter the service url and you will be able to see `Hello World!` from django view.


