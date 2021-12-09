app = "flask-app"

start:
	docker build -t ${app} .
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