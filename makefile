
BASEIMAGE := xycarto/anti-meridian
IMAGE := $(BASEIMAGE):2024-02-13

RUN ?= docker run -i --rm  \
	-u $$(id -u):$$(id -g) \
	-e DISPLAY=$$DISPLAY \
	-e RUN= \
	-v$$(pwd):/work \
	--net=host \
	-w /work $(IMAGE)


PHONY: 

anti-warp:
	$(RUN) python3 anti-meridian-warp.py $(in_file)

##### DOCKER #####

local-edit: Dockerfile
	docker run -it --rm --net=host \
	--user=$$(id -u):$$(id -g) \
	-e DISPLAY=$$DISPLAY \
	-e RUN= \
	-v$$(pwd):/work \
	-w /work \
	$(IMAGE)
	bash
	
docker-local: Dockerfile
	docker build --tag $(BASEIMAGE) - < Dockerfile && \
	docker tag $(BASEIMAGE) $(IMAGE)

docker: Dockerfile
	docker build --tag $(BASEIMAGE) - < Dockerfile && \
	docker tag $(BASEIMAGE) $(IMAGE) && \
	docker push $(IMAGE)

docker-pull:
	docker pull $(IMAGE)
