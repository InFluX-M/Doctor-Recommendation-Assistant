from elasticsearch import helpers
import json
from setting import get_es_client
import asyncio

class Search:
    def __init__(self, elastic_search_url: str = "https://localhost:9200") -> None:
        self.elastic = get_es_client(elastic_search_url)
        if not self.elastic.ping():
            raise Exception("Could not connect to Elasticsearch.")
        if not self.elastic.indices.exists(index="doctors"):
            self.init_es()

    def init_es(self, path_to_json: str = "data/doctors.json") -> None:
        mapping = {
            "mappings": {
                'properties': {
                    'display_name': {'type': 'text'},
                    'gender': {"type": "text", "fields": {"raw": {"type": "keyword"}}, "doc_values": True},
                    'calculated_rate': {'type': 'integer', "index": False, "doc_values": True},
                    'rates_count': {'type': 'integer', "index": False, "doc_values": True},
                    'insurances': {"type": "text", "fields": {"raw": {"type": "keyword"}}},
                    'number_of_visits': {'type': 'long', "index": False, "doc_values": True},
                    'expertise': {'type': 'text'},
                    'display_expertise': {'type': 'text'},
                    'display_address': {'type': 'text'},
                    'waiting_time': {'type': 'keyword', "doc_values": True},
                    'badges': {'type': 'keyword', "doc_values": True},
                    'centers': {'type': 'nested', 'properties': {
                        'status': {'type': 'integer', "index": False},
                        'name': {'type': 'text'},
                        'display_number': {'type': 'text', "index": False},
                        'address': {'type': 'text'},
                        'center_type': {'type': 'text', "index": False}
                    }},
                    'online_visit': {'type': 'boolean'},
                    'first_available_appointment': {'type': 'date', "format": "yyyy-MM-dd"},
                    'image': {'type': 'text', "index": False}
                }
            }
        }
        self.elastic.indices.create(index='doctors', body=mapping)
        with open(path_to_json, 'r', encoding='utf-8') as f:
            data: list[dict] = json.load(f)
        doctors = [
            {"_index": "doctors", "_op_type": "index", "_id": doctor.pop('id'), "_source": doctor}
            for doctor in data
        ]
        success, failed = helpers.bulk(self.elastic, doctors)
        print(f"Successfully indexed {success} documents, {failed} failed")
        return
    
    
class AsyncSearch:
    def __init__(self, elastic_search_url: str = "https://localhost:9200") -> None:
        self.elastic = get_es_client(elastic_search_url, get_async_client=True)
        if not asyncio.run(self.elastic.ping()):
            raise Exception("Could not connect to Elasticsearch.")
        if not self.elastic.indices.exists(index="doctors"):
            Search(elastic_search_url)
        
    async def query(self):
        pass

if __name__ == "__main__":
    s = Search()