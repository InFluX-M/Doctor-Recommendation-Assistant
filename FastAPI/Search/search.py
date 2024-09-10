from elasticsearch import helpers
import json
import asyncio
from typing import List, Dict
import jdatetime
from .setting import get_es_client

def convert_text_to_gregorian(text: str) -> str | None:
    if text == None:
        return None
    persian_numbers = {
        "یک": 1, "اول": 1, "دوم": 2, "دو": 2, "سوم": 3, "سه": 3, "چهار": 4, "چهارم": 4, "پنجم": 5, "پنج": 5, "ششم": 6, "شش": 6, "شیشم": 6, "شیش": 6, "هفتم": 7, "هفت": 7, "هشتم": 8, "هشت": 8, "نهم": 9, "نه": 9, "دهم": 10, "ده": 10, "یازدهم": 11, "یازده": 11, "دوازدهم": 12, "دوازده": 12, "سیزدهم": 13, "سیزده": 13, "چهاردهم": 14, "چهارده": 14, "پانزدهم": 15, "پانزده": 15, "پونزدهم": 15, "پونزده": 15, "شانزدهم": 16, "شانزده": 16, "شونزدهم": 16, "شونزده": 16, "هفدهم": 17, "هفده": 17, "هیفدهم": 17, "هیفده": 17, "هجدهم": 18, "هجده": 18, "هیجدهم": 18, "هیجده": 18, "نوزدهم": 19, "نوزده": 19, "بیستم": 20, "بیست": 20, "نیمه": 15, "اواسط": 15
    }
    def convert_to_number(persian_text: str) -> int:
        persian_text = persian_text.strip()
        if persian_text in persian_numbers:
            return persian_numbers[persian_text]
        parts = persian_text.split(" و ")
        number = 0
        for part in parts:
            if part in persian_numbers:
                number += persian_numbers[part]
        return number if number > 0 else None
    
    text = text.split(' ')
    if text[0] in ['امروز', 'کمتر']:
        date = jdatetime.date.today()
    elif text[0] == 'فردا':
        date = jdatetime.date.today() + jdatetime.timedelta(days=1)
    elif 'پس فردا' in text:
        date = jdatetime.date.today() + jdatetime.timedelta(days=2)
    elif 'هفته' in text:
        if 'بعد' in text:
            date = jdatetime.date.today() + jdatetime.timedelta(days= 6 - jdatetime.date.today().weekday(), weeks=1)
        else:
            date = jdatetime.date.today() + jdatetime.timedelta(days= 6 - jdatetime.date.today().weekday())
    elif 'ماه' in text:
        month = jdatetime.date.today().month
        year = jdatetime.date.today().year
        if month < 11 and 'بعد' in text:
            month += 2
        elif month > 10 and 'بعد' in text:
            month = (month + 2) % 12
            year += 1
        elif month < 12:
            month += 1
        else:
            month = 1
            year += 1
        date = jdatetime.date(year=year, month=month, day=1) - jdatetime.timedelta(days= 1)
    else:
        if text[0].isdigit():
            day = int(text[0])
            month = jdatetime.date.j_month_fa_to_num(text[1])
        else:
            index = -1
            for m in jdatetime.date.j_months_fa:
                index = text.find(m)
                if index != -1:
                    month = m
                    break
            if index != -1:
                day = convert_to_number(text[:index])
                month = jdatetime.date.j_month_fa_to_num(month)
            else:
                return None
        year = jdatetime.date.today().year
        if jdatetime.date.today().month > month:
            year += 1
        date = jdatetime.date(year, month, day)
    gregorian_datetime = date.togregorian()
    return str(gregorian_datetime)

class AsyncSearch:
    def __init__(self, elastic_search_url: str = "https://es01:9200") -> None:
        self.elastic_search_url = elastic_search_url
        self.elastic = None

    async def initialize(self) -> None:
        self.elastic = get_es_client(self.elastic_search_url, get_async_client=True)
        if not await self.elastic.ping():
            raise Exception("Could not connect to Elasticsearch.")
        if not await self.elastic.indices.exists(index="doctors"):
            self._init_es()
        
    async def _init_es(self, path_to_json: str = "Search/doctors.json") -> None:
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

        await self.elastic.indices.create(index='doctors', body=mapping)
        with open(path_to_json, 'r', encoding='utf-8') as f:
            data: List[Dict] = json.load(f)
        doctors = [
            {"_index": "doctors", "_op_type": "index", "_id": doctor.pop('index'), "_source": doctor}
            for doctor in data
        ]
        success, failed = await helpers.bulk(self.elastic, doctors)
        print(f"Successfully indexed {success} documents, {failed} failed")
        return

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
                {"_score": {"order": "desc"}}, 
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
            date = convert_text_to_gregorian(keyword['apt'])
            query["query"]["bool"]['must'].append({
                "range": {"first_available_appointment": {"lte": date}}
            })

        if 'cnd' in keyword:
            query["query"]["bool"]['should'].append({
                "multi_match": {
                    "query": keyword['cnd'],
                    "type": "cross_fileds",
                    "fields": ['display_expertise', 'expertise']
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
            query["query"]["bool"]['should'].append({
                "match": {"display_expertise": keyword['srt']}
            })

        if 'spy' in keyword:
            query["query"]["bool"]['must'].append({
                "multi_match": {
                    "query": keyword['spy'],
                    "type": "cross_fileds",
                    "fields": ['display_expertise', 'expertise']
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
    
    async def close(self) -> None:
        await self.elastic.close()