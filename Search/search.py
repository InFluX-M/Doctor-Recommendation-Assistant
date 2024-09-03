from elasticsearch import helpers
import json
from setting import get_es_client
import asyncio

import sys
import os
sys.path.append(os.path.abspath('.'))
from DataGathering.preprocess import Doctor

class Search:
    def __init__(self, elastic_search_url: str = "https://localhost:9200") -> None:
        self.elastic = get_es_client(elastic_search_url)
        if not self.elastic.ping():
            raise Exception("Could not connect to Elasticsearch.")
        if not self.elastic.indices.exists(index="doctors"):
            self.init_es()

    def init_es(self, path_to_json: str = "data/doctors.json") -> None:
        mapping = {
            "settings": {
                "analysis": {
                "filter": {
                    "gender_synonym_filter": {
                    "type": "synonym",
                    "synonyms": [
                        'مرد, آقا, مذکر, نر, رجل, پسر',
                        'زن, خانم, خانوم, دختر, مونث, مادام, بانو'
                    ]
                    }
                },
                "analyzer": {
                    "gender_analyzer": {
                    "tokenizer": "standard",
                    "filter": [
                        "gender_synonym_filter"
                    ]
                    }
                }
                }
            },
            "mappings": {
                'properties': {
                    'display_name': {'type': 'text'},
                    'gender': {"type": "text", "analyzer": "gender_analyzer", "doc_values": True},
                    'calculated_rate': {'type': 'integer', "index": False, "doc_values": True},
                    'rates_count': {'type': 'integer', "index": False, "doc_values": True},
                    'insurances': {"type": "text"},
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
        if not self.elastic.ping():
            raise Exception("Could not connect to Elasticsearch.")
        if not self.elastic.indices.exists(index="doctors"):
            Search(elastic_search_url)
    async def query(self, keyword: dict):
        query = {
            'must': []
        }
        if 'apt' in keyword:
            date = Doctor.convert_text_to_gregorian(keyword['apt'])
            query['must'].append({"range": {"date": {"lte": date}}})
        if 'loc' in keyword:
            query['must'].append({
                "should": [
                    {"match": {"display_address": keyword['loc']}},
                    {"nested": {"path": "centers", "query": {"match" : {"centers.address": keyword['loc']}}}}
                ]
            })
        if 'cnd' in keyword:
            query['must'].append({"should": [
                {"multi_match": {"query": keyword['cnd'], "type": "cross_fields", "fields": ["display_expertise", "expertise"]}}
            ], "minimum_should_match": 0})
        if 'gnd' in keyword:
            query['must'].append({"match": {"gender": keyword['gnd']}})
        if 'inc' in keyword:
            query['must'].append({"match": {"insurances": keyword['inc']}})
        if 'srt' in keyword:
            query['must'].append({"match": {"display_expertise": keyword['srt']}})
        if 'spy' in keyword:
            query['must'].append({"should": [{"multi_match": {"query": keyword['spy'], "type": "cross_fields", "fields": ["display_expertise", "expertise"]}}]})
        if 'trt' in keyword:
            query['must'].append({"should": [{"term": {"badges": keyword['trt']}}], "minimum_should_match": 0})
        if 'vtp' in keyword:
            if keyword['vtp'] in ["آنلاین", "غیرحضوری", "غیر حضوری", "مجازی", "اینترنتی", "برخط", "بر خط"]:
                query['must'].append({"should": [{"term": {"online_visit": True}}], "minimum_should_match": 0})

        response = await self.elastic.search(index="doctors", body={"query": {"bool": query}})
        return response


async def main():
    s = AsyncSearch()
    result = await s.query(keyword={'loc': "مشهد بلوار خیام", 'gnd': "آقا", 'spy': "قلب"})
    print(result)
if __name__ == "__main__":
    asyncio.run(main())