import time, os
import subprocess

from datadog import initialize, statsd
from ddtrace import tracer, patch
from ddtrace.contrib.flask import TraceMiddleware

try:
    initialize(statsd_host=os.environ['DOGSTATSD_HOST_IP'], statsd_port=8125)
    tracer.configure(
    hostname=os.environ['DD_AGENT_SERVICE_HOST'],
    port=os.environ['DD_AGENT_SERVICE_PORT'],
)

except:
    print("No environment variables for Datadog set. App won't be instrumented.")

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)

#patch traceware
traced_app = TraceMiddleware(app, tracer, service="video-inference-app", distributed_tracing=True)

#logging stuff
import logging
import json_log_formatter
import threading

# for correlating logs and traces

FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')
logging.basicConfig(format=FORMAT)

try:
    formatter = json_log_formatter.JSONFormatter()
    json_handler = logging.FileHandler(filename='/var/log/flask/mylog.json')
    json_handler.setFormatter(formatter)
    logger = logging.getLogger('my_json')
    logger.addHandler(json_handler)
    logger.setLevel(logging.INFO)
except:
    print("File logger not configured")

@app.route('/video-inference', methods=['POST'])
def video_inference():
    params = request.get_json()
    subprocess.call(['python3',
                     'video-to-json.py',
                     '--video',
                     params['filename'],
                     '--post-url',
                     params['postback_url']])
    return jsonify({'message': 'received'})

@app.route('/')
def hello_world():
    return 'Hello world!'

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5007)
