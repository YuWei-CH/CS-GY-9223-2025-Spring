### Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v3.2.1/prometheus-3.2.1.linux-amd64.tar.gz

tar xvfz prometheus-*.tar.gz

cd prometheus-3.2.1.linux-amd64/

### Install Alertmanager
wget https://github.com/prometheus/alertmanager/releases/download/v0.28.1/alertmanager-0.28.1.linux-amd64.tar.gz

tar xvfz alertmanager-*.tar.gz

alertmanager-0.28.1.linux-amd64/

### Create an webhooks
https://api.slack.com/messaging/webhooks

curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/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


### Configure Prometheus
touch prometheus.yml
touch probe-alerts.yml

./alertmanager --config.file=alertmanager.yml &


### Testing the Alerting System

cd ../prometheus-3.2.1.linux-amd64/

./prometheus --config.file=prometheus.yml &

curl http://a178b2df693a147af84fb7579c29c31a-115792124.us-east-2.elb.amazonaws.com/toggle-health

(Webui)
http://localhost:9090

(Clean UP)
ps aux | grep prometheus
kill <prometheus_pid>

ps aux | grep alertmanager
kill <alertmanager_pid>