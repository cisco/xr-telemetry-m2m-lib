#
# Dockerfile for basic Go environment
#
FROM ubuntu:14.04
MAINTAINER Simon Chatterjee <sichatte@cisco.com>

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y golang man git openssh-client

RUN mkdir /go
ENV GOPATH=/go:/code/xrm2m
ENV PATH=/code/xrm2m/bin:/usr/bin:/bin

# golang.org/x/crypto/ssh doesn't have aes128-cbc in august 2015
RUN go get github.com/ScriptRock/crypto/ssh
RUN go get github.com/kr/pretty
RUN go get github.com/abiosoft/ishell
