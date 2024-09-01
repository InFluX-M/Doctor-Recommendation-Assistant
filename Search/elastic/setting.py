# settings.py

from elasticsearch import Elasticsearch

def get_es_client(url="https://localhost:9200"):
    """
    Create and return an Elasticsearch client.
    docker cp elastic-es01-1:/usr/share/elasticsearch/config/certs .
    """
    return Elasticsearch(
        url,
        ca_certs="./certs/ca/ca.crt",
        basic_auth=("elastic", "456$%^rtyRTY")
    )

def get_number_of_replicas(es_client, index_name):
    """
    Get the number of replicas for a given index.
    """
    try:
        settings = es_client.indices.get_settings(index=index_name)
        number_of_replicas = settings[index_name]['settings']['index']['number_of_replicas']
        return number_of_replicas
    except Exception as e:
        return str(e)

def count_shards(es_client, index_name):
    """
    Count the number of primary and replica shards for a given index.
    """
    try:
        settings = es_client.indices.get_settings(index=index_name)
        number_of_shards = int(settings[index_name]['settings']['index']['number_of_shards'])
        number_of_replicas = int(settings[index_name]['settings']['index']['number_of_replicas'])
        total_shards = number_of_shards * (number_of_replicas + 1)
        
        return {
            "number_of_primary_shards": number_of_shards,
            "number_of_replica_shards": number_of_shards * number_of_replicas,
            "total_shards": total_shards
        }
    except Exception as e:
        return str(e)
