# bittrex-heikin-ashi-exporter

A prometheus exporter for <https://bittrex.com/Home/Markets>, but this time calculates the Heikin-Ashi candlestick values.

[Docker image can be found here](https://hub.docker.com/r/bcawthra/bittrex-heikin-ashi-exporter/).

# Developing Locally

- This requires a few Python modules, most notably `prometheus_client`.

```
python bittrex-heikin-ashi.py
```

- Curl the endpoint to verify it is collecting metrics:

```
curl http://localhost:9101/metrics
```

# Building the Docker Image

- Build the image:

```
docker build -t bittrex-heikin-ashi-exporter:latest .
```

- Run it while listening on localhost:9101:

```
docker run --rm -p 127.0.0.1:9101:9101 bittrex-heikin-ashi-exporter:latest
```

- Run it interactively:

```
docker run --rm -it --entrypoint=/bin/bash -p 127.0.0.1:9101:9101 bittrex-heikin-ashi-exporter:latest
```

- You should be able to curl the endpoint as above.

# Testing the Prometheus Grafana Stack

- In the `prometheus-compose` directory, run:

```
docker-compose up
```

- Go to <http://localhost:3000>.  Log in as `admin/admin`. 

# Thanks and Links

- Bittrex API link - <https://bittrex.com/home/api>
- Prometheus exporters - <https://prometheus.io/docs/instrumenting/writing_exporters/>
- Writing JSON exporters in Python from Robust Perception - <https://www.robustperception.io/writing-json-exporters-in-python/>
- Grafana Dashboard - <https://grafana.com/dashboards/3890>

