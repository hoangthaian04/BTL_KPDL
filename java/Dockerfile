FROM maven:3.9.9-eclipse-temurin-17 AS builder

WORKDIR /build
COPY java/pom.xml pom.xml
COPY java/src src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:17-jre-jammy

WORKDIR /opt/btl_kpdl

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python-is-python3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY python/requirements.txt /tmp/python-requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/python-requirements.txt

COPY --from=builder /build/target/*.jar /opt/btl_kpdl/app.jar
COPY python /opt/btl_kpdl/python
COPY Telco_customer_churn.xlsx /opt/btl_kpdl/Telco_customer_churn.xlsx

RUN mkdir -p /opt/btl_kpdl/java/tmp /opt/btl_kpdl/python/artifacts/charts

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/opt/btl_kpdl/app.jar"]
