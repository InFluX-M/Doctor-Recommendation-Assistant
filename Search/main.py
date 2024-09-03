from elasticsearch import Elasticsearch
from setting import get_es_client, get_number_of_replicas, count_shards

# Initialize Elasticsearch client
es = get_es_client("https://localhost:9200") 

# Define the index name
index_name = "mahmat"

print(es.ping())

print(count_shards(es, index_name))

resp = es.indices.get_mapping(
    index="mahmat",
)
print(resp)

