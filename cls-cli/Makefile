.PHONY: build clean install

BINARY=cls-cli
VERSION=0.1.0
LDFLAGS=-ldflags "-s -w -X main.Version=$(VERSION)"

build:
	go build $(LDFLAGS) -o $(BINARY) .

install:
	go install $(LDFLAGS) .

clean:
	rm -f $(BINARY)

test:
	go test ./...

fmt:
	go fmt ./...

vet:
	go vet ./...
