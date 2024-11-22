import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

bucket = "default"
org = "default"
token = "TK6Ys6-W6gYA7Id7lOQVqWj2yElTUC6I6q_MpG2rsqNPXDbvRR0INp1gwGmCA0qh-SXf7G7WxM00r7A9xFcoUg=="
# Store the URL of your InfluxDB instance
url="http://127.0.0.1:8086"

client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

# Write script
write_api = client.write_api(write_options=SYNCHRONOUS)

p = influxdb_client.Point("my_measurement").tag("location", "Prague").field("temperature", 25.3)
write_api.write(bucket=bucket, org=org, record=p)
