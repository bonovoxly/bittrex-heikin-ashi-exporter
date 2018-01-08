from datetime import datetime, timedelta
from prometheus_client import start_http_server, Metric, REGISTRY
import argparse
import json
import logging
import requests
import sys
import time

# logging setup
log = logging.getLogger('bittrex-signals-exporter')
log.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

class BittrexHeikinAshi():
  def __init__(self, host, prometheusport, query):
    self.query = query
    self.prometheus = ''.join(['http://', host, ':', prometheusport, '/api/v1/query?query=', query])
    # time ranges in minutes; 30min, 1hr(60), 6hr(360), 12hr(720), 1d(1440), 1w(10080)
    self.ranges = {'30m': 30, '1h': 60, '6h': 360, '12h' :720, '1d': 1440, '1w': 10080}

  def collect(self):
    # get current information
    date = datetime.utcnow()
    # get current values from the bittrex-exporter
    currentvalue = requests.get(self.prometheus)
    currentvaluer = json.loads(currentvalue.content.decode('UTF-8'))
    currenthigh = {}
    currentlow = {}
    currentclose = {}
    for it in currentvaluer['data']['result']:
      if it['metric']['Type'] == 'High':
        currenthigh[it['metric']['MarketName']] = float(it['value'][1])
      if it['metric']['Type'] == 'Low':
        currentlow[it['metric']['MarketName']] = float(it['value'][1])
      if it['metric']['Type'] == 'Last':
        currentclose[it['metric']['MarketName']] = float(it['value'][1])
    # setup the resposemetric
    metrictime = Metric('bittrex_heikinashi_response_time', 'Total time for the Prometheus API to respond.', 'summary')
    metrictime.add_sample('bittrex_heikinashi_response_time', value=float(currentvalue.elapsed.total_seconds()), labels={'Name': self.prometheus, 'Range': 'current', 'query': self.query})
    metric = Metric('bittrexheikinashi', 'Bittrex Heikin-Ashi metric values', 'gauge')
    for k, v in self.ranges.items():
      # get date window
      daterun = date - timedelta(minutes=v)
      daterunstart = date - timedelta(minutes=v*2)
      # log some info
      log.info(k)
      log.info(''.join([self.prometheus, '&time=', daterun.strftime("%Y-%m-%dT%H:%M:%SZ")]))
      log.info(''.join([self.prometheus, '&time=', daterunstart.strftime("%Y-%m-%dT%H:%M:%SZ")]))
      # get end of window
      value = requests.get(''.join([self.prometheus, '&time=', daterun.strftime("%Y-%m-%dT%H:%M:%SZ")]))
      valuer = json.loads(value.content.decode('UTF-8'))
      metrictime.add_sample('bittrex_heikinashi_response_time', value=float(value.elapsed.total_seconds()), labels={'Name': self.prometheus, 'Range': k, 'query': self.query})
      # get start of window
      valuestart = requests.get(''.join([self.prometheus, '&time=', daterunstart.strftime("%Y-%m-%dT%H:%M:%SZ")]))
      valuestartr = json.loads(valuestart.content.decode('UTF-8'))
      metrictime.add_sample('bittrex_heikinashi_response_time', value=float(value.elapsed.total_seconds()), labels={'Name': self.prometheus, 'Range': 'x'.join([k, '2']), 'query': self.query})
      # to calculate the Heikin-Ashi xClose(average price of the current window)
      xcloseopen = {}
      for each in valuer['data']['result']:
        if each['metric']['Type'] == 'Last':
          xcloseopen[each['metric']['MarketName']] = float(each['value'][1])
      xclose = {}
      for key,value in currentclose.items():
        if key in xcloseopen:
          xclose[key] = ( xcloseopen[key] + currenthigh[key] + currentlow[key] + currentclose[key] ) / 4
          metric.add_sample('bittrexheikinashi', value=float(( xcloseopen[key] + currenthigh[key] + currentlow[key] + currentclose[key] ) / 4), labels={'MarketName': key, 'Range': k, 'Type': 'xClose'})
      # calculate the Heikin-Ashi xOpen (midpoint of the previous bar)
      xopenopen = {}
      for each in valuestartr['data']['result']:
        if each['metric']['Type'] == 'Last':
          xopenopen[each['metric']['MarketName']] = float(each['value'][1])
      xopenclose = {}
      for each in valuer['data']['result']:
        if each['metric']['Type'] == 'Last':
          xopenclose[each['metric']['MarketName']] = float(each['value'][1])
      xopen = {}
      for key,value in currentclose.items():
        if key in xopenopen and key in xopenclose:
          xopen[key] = ( xopenopen[key] + xopenclose[key] ) / 2
          metric.add_sample('bittrexheikinashi', value=float(( xopenopen[key] + xopenclose[key] ) / 2), labels={'MarketName': key, 'Range': k, 'Type': 'xOpen'})
      # calculate the Heikin-Ashi xHigh (highest value in the set)
      xhigh = {}
      for key,value in currenthigh.items():
        if key in xopen and key in xclose:
          input = [value, xopen[key], xclose[key]]
          xhigh[key] = max(input, key=float)
          metric.add_sample('bittrexheikinashi', value=float(max(input, key=float)), labels={'MarketName': key, 'Range': k, 'Type': 'xHigh'})
      # calculate the Heikin-Ashi xLow (lowest value in the set)
      xlow = {}
      for key,value in currentlow.items():
        if key in xopen and key in xclose:
          input = [value, xopen[key], xclose[key]]
          xlow[key] = min(input, key=float)
          metric.add_sample('bittrexheikinashi', value=float(min(input, key=float)), labels={'MarketName': key, 'Range': k, 'Type': 'xLow'})
    yield metrictime
    yield metric

if __name__ == '__main__':
  try:
    parser = argparse.ArgumentParser(
      description=__doc__,
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port', nargs='?', const=9101, help='The TCP port to listen on.  Defaults to 9101.', default=9101)
    parser.add_argument('--host', nargs='?', help='The Prometheus server to query. Defaults to localhost.', default='localhost')
    parser.add_argument('--prometheusport', nargs='?', help='The Prometheus port. Defaults to 9090.', default='9090')
    parser.add_argument('--query', nargs='?', help='The Prometheus metric to query. Defaults to bittrex.', default='bittrex')
    args = parser.parse_args()
    log.info(args.port)
  
    REGISTRY.register(BittrexHeikinAshi(args.host, args.prometheusport, args.query))
    start_http_server(int(args.port))
    while True:
      time.sleep(60)
  except KeyboardInterrupt:
    print(" Interrupted")
    exit(0)
