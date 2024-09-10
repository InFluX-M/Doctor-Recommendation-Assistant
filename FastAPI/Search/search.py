from elasticsearch import helpers
import json
from setting import get_es_client
import asyncio
from typing import List, Dict
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
                    "char_filter": {
                        "zero_width_spaces": {
                            "type": "mapping",
                            "mappings": ["\\u200C=>\\u0020"]
                        }
                    },
                    "filter": {
                        "persian_stop": {
                            "type": "stop",
                            "stopwords": "_persian_"
                        },
                        "gender_synonym_filter": {
                            "type": "synonym",
                            "synonyms": [
                                "مرد, آقا, مذکر, نر, رجل, پسر",
                                "زن, خانم, خانوم, دختر, مونث, مادام, بانو"
                            ]
                        }
                    },
                    "analyzer": {
                        "rebuilt_persian": {
                            "tokenizer": "standard",
                            "char_filter": ["zero_width_spaces"],
                            "filter": [
                                "lowercase",
                                "decimal_digit",
                                "arabic_normalization",
                                "persian_normalization",
                                "persian_stop"
                            ]
                        },
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
                "properties": {
                    "display_name": {"type": "text"},
                    "gender": {"type": "text", "analyzer": "gender_analyzer"},
                    "calculated_rate": {"type": "integer", "index": False},
                    "rates_count": {"type": "integer", "index": False},
                    "insurances": {"type": "text"},
                    "number_of_visits": {"type": "long", "index": False},
                    "expertise": {"type": "text", 'analyzer': 'rebuilt_persian'},
                    "display_expertise": {"type": "text", 'analyzer': 'rebuilt_persian'},
                    "waiting_time": {"type": "integer"},
                    "badges": {"type": "keyword"},
                    "centers": {
                        "type": "nested",
                        "properties": {
                            "status": {"type": "integer", "index": False},
                            "name": {"type": "text"},
                            "display_number": {"type": "text", "index": False},
                            "province_name": {"type": "keyword"},
                            "city_name": {"type": "keyword"},
                            "address": {"type": "text", 'analyzer': 'rebuilt_persian'},
                            "center_type": {"type": "text", "index": False}
                        }
                    },
                    "online_visit": {"type": "boolean"},
                    "first_available_appointment": {"type": "date", "format": "yyyy-MM-dd"},
                    "url": {"type": "text", "index": False}
                }
            }
        }

        self.elastic.indices.create(index='doctors', body=mapping)
        with open(path_to_json, 'r', encoding='utf-8') as f:
            data: List[Dict] = json.load(f)
        doctors = [
            {"_index": "doctors", "_op_type": "index", "_id": doctor.pop('index'), "_source": doctor}
            for doctor in data
        ]
        success, failed = helpers.bulk(self.elastic, doctors)
        print(f"Successfully indexed {success} documents, {failed} failed")
        return

    def delete_data(self) -> None:
        if self.elastic.indices.exists(index="doctors"):
            self.elastic.indices.delete(index="doctors")

    def query(self, keyword: dict) -> dict:
        query = {
            'query': {
                "bool": {
                "must": [],
                "should": [{"terms": {"badges": ['خوش برخورد', 'کمترین معطلی', 'منتخب پذیرش24']}}],
                "minimum_should_match": 0
                }
            },
            'sort': [
                {"calculated_rate": {"order": "desc"}}, 
                {"waiting_time": {"order": "asc"}},
                {"rates_count": {"order": "desc"}}, 
                {"number_of_visits": {"order": "desc"}}, 
            ],
            'size': 5
        }

        if 'loc' in keyword:
            with open('data/cities.csv', 'r', encoding='utf-8') as f:
                cities = [city.replace('\n', '') for city in f.readlines()]
            city = None
            address = None
            for word in keyword['loc'].copy():
                if word in cities:
                    city = word
                    keyword['loc'].remove(city)
            if keyword['loc']:
                address = ' '.join(keyword['loc'])
            loc = []
            if city:
                loc.append({'term': {"centers.city_name": {'value': city}}})
            if address:
                loc.append({'match': {'centers.address': address}})
            query["query"]["bool"]['must'].append({
                "nested": {
                    "path": "centers",
                    "query": {'bool': {'must': loc}}
                }
            })

        if 'apt' in keyword:
            date = Doctor.convert_text_to_gregorian(keyword['apt'])
            query["query"]["bool"]['must'].append({
                "range": {"first_available_appointment": {"lte": date}}
            })

        if 'cnd' in keyword:
            query["query"]["bool"]['should'].append({
                "multi_match": {
                    "query": keyword['cnd'],
                    "type": "cross_fields",
                    "fields": ["display_expertise", "expertise"]
                }
            })

        if 'gnd' in keyword:
            query["query"]["bool"]['must'].append({
                "match": {"gender": keyword['gnd']}
            })

        if 'inc' in keyword:
            query["query"]["bool"]['should'].append({
                "match": {"insurances": keyword['inc']}
            })

        if 'srt' in keyword:
            query["query"]["bool"]['must'].append({
                "match": {"display_expertise": keyword['srt']}
            })

        if 'spy' in keyword:
            query["query"]["bool"]['must'].append({
                "multi_match": {
                    "query": keyword['spy'],
                    "type": "cross_fields",
                    "fields": ["display_expertise", "expertise"]
                }
            })

        if 'trt' in keyword:
            query["query"]["bool"]['must'].append({
                "terms": {"badges": ['خوش برخورد']}
            })

        if 'vtp' in keyword:
            if keyword['vtp'] in ["آنلاین", "غیرحضوری", "غیر حضوری", "مجازی", "اینترنتی", "برخط", "بر خط"]:
                query["query"]["bool"]['must'].append({
                    "term": {"online_visit": True}
                })

        response = self.elastic.search(index="doctors", body={"query": query})
        return response


class AsyncSearch:
    def __init__(self, elastic_search_url: str = "https://localhost:9200") -> None:
        self.elastic_search_url = elastic_search_url
        self.elastic = None

    async def initialize(self) -> None:
        self.elastic = get_es_client(self.elastic_search_url, get_async_client=True)
        if not await self.elastic.ping():
            raise Exception("Could not connect to Elasticsearch.")
        if not await self.elastic.indices.exists(index="doctors"):
            Search(self.elastic_search_url)

    async def delete_data(self) -> None:
        if await self.elastic.indices.exists(index="doctors"):
            await self.elastic.indices.delete(index="doctors")

    async def query(self, keyword: dict) -> list[dict]:
        query = {
            'query': {
                "bool": {
                    "must": [],
                    "should": [{"terms": {"badges": ['خوش برخورد', 'کمترین معطلی', 'منتخب پذیرش24']}}],
                    "minimum_should_match": 0
                }
            },
            'sort': [
                {"calculated_rate": {"order": "desc"}}, 
                {"waiting_time": {"order": "asc"}},
                {"rates_count": {"order": "desc"}}, 
                {"number_of_visits": {"order": "desc"}}, 
            ],
            'size': 5
        }

        if 'loc' in keyword:
            with open('data/cities.csv', 'r', encoding='utf-8') as f:
                cities = [city.replace('\n', '') for city in f.readlines()]
            city = None
            address = None
            for word in keyword['loc'].copy():
                if word in cities:
                    city = word
                    keyword['loc'].remove(city)
            if keyword['loc']:
                address = ' '.join(keyword['loc'])
            loc = []
            if city:
                loc.append({'term': {"centers.city_name": {'value': city}}})
            if address:
                loc.append({'match': {'centers.address': address}})
            query["query"]["bool"]['must'].append({
                "nested": {
                    "path": "centers",
                    "query": {'bool': {'must': loc}}
                }
            })

        if 'apt' in keyword:
            date = Doctor.convert_text_to_gregorian(keyword['apt'])
            query["query"]["bool"]['must'].append({
                "range": {"first_available_appointment": {"lte": date}}
            })

        if 'cnd' in keyword:
            query["query"]["bool"]['should'].append({
                "multi_match": {
                    "query": keyword['cnd'],
                    "type": "cross_fields",
                    "fields": ["display_expertise", "expertise"]
                }
            })

        if 'gnd' in keyword:
            query["query"]["bool"]['must'].append({
                "match": {"gender": keyword['gnd']}
            })

        if 'inc' in keyword:
            query["query"]["bool"]['should'].append({
                "match": {"insurances": keyword['inc']}
            })

        if 'srt' in keyword:
            query["query"]["bool"]['must'].append({
                "match": {"display_expertise": keyword['srt']}
            })

        if 'spy' in keyword:
            query["query"]["bool"]['must'].append({
                "multi_match": {
                    "query": keyword['spy'],
                    "type": "cross_fields",
                    "fields": ["display_expertise", "expertise"]
                }
            })

        if 'trt' in keyword:
            query["query"]["bool"]['must'].append({
                "terms": {"badges": ['خوش برخورد']}
            })

        if 'vtp' in keyword:
            if keyword['vtp'] in ["آنلاین", "غیرحضوری", "غیر حضوری", "مجازی", "اینترنتی", "برخط", "بر خط"]:
                query["query"]["bool"]['must'].append({
                    "term": {"online_visit": True}
                })

        response = await self.elastic.search(index="doctors", body=query)
        return [hit['_source'] for hit in response['hits']['hits']]
    

if __name__ == "__main__":
    async def main(keyword: dict):
        s = AsyncSearch()
        await s.initialize()
        result = await s.query(keyword=keyword)
        print(result)
    asyncio.run(main(keyword={'loc': ["مشهد"], 'gnd': 'خانوم', 'spy': 'مغز و اعصاب'}))
    # s = Search()
    # result = s.query()
    # print(result['hits'])