# Image name: landerlini/vktestset-rclone-bind:latest
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y -q \
      openssh-client \
      openssh-server \
      fuse3 \
      unzip \
      curl 

RUN curl https://rclone.org/install.sh | bash

      
