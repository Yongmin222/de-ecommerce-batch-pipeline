FROM bitnamilegacy/spark:latest

USER root
RUN install_packages curl

RUN curl -o /opt/bitnami/spark/jars/mysql-connector-j.jar \
    https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar
