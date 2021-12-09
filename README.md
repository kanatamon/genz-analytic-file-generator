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