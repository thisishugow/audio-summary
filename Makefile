VERSION := $(shell poetry version --short)
all: build buildimg clean

build:
	@rm -rf .tmpbuild || true
	@mkdir -p .tmpbuild
	poetry build -o .tmpbuild

buildimg:
	@podman build -t audio-summary:$(VERSION) --platform linux/amd64 .

clean:
	@rm -rf .tmpbuild || true
	@podman rmi $$(podman images -f "dangling=true" -q) || true

.PHONY: build

