app = "flask-app"
app_prod = "flask-app-prod"

start:
	docker build -t ${app} -f Dockerfile.dev .
	docker run -d -p 5000:80 \
		--name=${app} \
		-v ${PWD}:/app ${app}

stop:
	docker stop ${app}
	docker rm ${app}

shell:
	docker exec -it ${app} /bin/bash

logs:
	docker logs -f ${app}

prod:
	docker build -t ${app_prod} -f Dockerfile .
	docker run -d -p 4321:4321 \
		--name=${app_prod} \
		${app_prod}