FROM mihxil/npo-pyapi-make:latest

RUN apk upgrade && apk add --no-cache openjdk8-jre openssh-client && \
    wget https://github.com/jiaqi/jmxterm/releases/download/v1.0.2/jmxterm-1.0.2-uber.jar -O /root/jmxterm.jar

ADD ssh_config /root
ENV JMXTERM_BINARY=/root/jmxterm.jar
RUN (cd /work && git clone https://github.com/npo-poms/scripts.git)

ENTRYPOINT "/usr/bin/make"

