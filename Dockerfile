FROM python:3.6
RUN pip install prometheus_client requests
RUN mkdir -p /opt/bittrex-heikin-ashi-exporter
COPY ./Dockerfile /opt/bittrex-heikin-ashi-exporter/
COPY ./README.md /opt/bittrex-heikin-ashi-exporter/
COPY ./bittrex-heikin-ashi.py /opt/bittrex-heikin-ashi-exporter/
WORKDIR /opt/bittrex-heikin-ashi-exporter

ENTRYPOINT ["python3", "bittrex-heikin-ashi.py"]
