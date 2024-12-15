FROM ubuntu:latest
LABEL authors="nic"

ENTRYPOINT ["top", "-b"]