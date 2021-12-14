# Analytic File Generator Service

## Development

### Prerequisites

- Docker installed on the machine
- Provide credentials in `.env`
- _[Required if you want to run app via Make]_ Makefile installed

### Running via Make

- To run the application on your machine

   ```sh
   make start

   # Running on http://127.0.0.1:5000/
   ```

- To stop the application

   ```sh
   make stop
   ```

- To shell into the running container

   ```sh
   make shell
   ```

- To get the command line output of your app

   ```sh
   make logs
   ```

### Running via VS-Code Remote Container

See instructions to get started → https://code.visualstudio.com/docs/remote/containers

After successfully ran the `Dev Container: Flask App`

1. Open the VS-Code's terminal to shell into the container
2. Start the flask application with debug mode

   ```sh
   # Set debug mode
   export FLASK_ENV=development

   # Start the flask application
   flask run

   # Running on http://127.0.0.1:5000/
   ```

## Deployment

We use [dokku](https://dokku.com/docs/deployment/application-deployment/) for deployment.

### Prerequisites

- Make sure your already added public-key on the reg's dokku server (172.16.0.6)

   ```sh
   # At dokku server
   you@dokku:~$ dokku ssh-keys:add KEY_NAME path/to/id_rsa.pub

   # Read more -> https://dokku.com/docs/deployment/user-management/#adding-ssh-keys
   ```

- Make sure a dokku's app has already created on the reg's dokku server

   ```sh
   # At dokku server
   you@dokku:~$ dokku apps:create <APP_NAME>
   ```

- Make sure to setup env on the dokku's app (can be configured anytime)

   ```sh
   # At dokku server
   you@dokku:~$ dokku config:set <APP_NAME> \
      DB_HOST=172.16.0.8 \
      DB_USER=... \
      DB_PASS=... \
      DB_NAME=zcmu_survey
   ```

### Start deployment

```sh
# Add remote
git remote add dokku dokku@172.16.0.6:genz-analytic-file-gen

# Start deployment
git push dokku main:master

# Running on http://172.16.0.6:4321/
```