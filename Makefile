IMAGENAME?=sayadrameez/redmine_exporter
TAG?=latest
REDMINE_SERVER?=https://myredmine

debug: image
	docker run --rm -p 9121:9121 -e DEBUG=1 -e REDMINE_SERVER=$(REDMINE_SERVER) -e VIRTUAL_PORT=9121 $(IMAGENAME):$(TAG)

image:
	docker build -t $(IMAGENAME):$(TAG) .

push: image
	docker push $(IMAGENAME):$(TAG)


.PHONY: image push debug