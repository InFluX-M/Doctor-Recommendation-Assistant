# settings.py

from elasticsearch import AsyncElasticsearch, Elasticsearch

def get_es_client(url: str = "https://es01:9200", get_async_client: bool = False) -> Elasticsearch | AsyncElasticsearch:
    """
    Create and return an Elasticsearch client.
    docker cp search-es01-1:/usr/share/elasticsearch/config/certs .
    """
    if get_async_client:
        return AsyncElasticsearch(
            url,
            ca_certs="Search/certs/ca/ca.crt",
            basic_auth=("elastic", "456$%^rtyRTY")
        )
    else:
        return Elasticsearch(
            url,
            ca_certs="Search/certs/ca/ca.crt",
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
