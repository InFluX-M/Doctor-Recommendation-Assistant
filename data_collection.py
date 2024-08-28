import requests as req
import re
import json
import pandas as pd
import time
from random import random
import logging


class Paziresh24:
    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            response = req.get("https://apigw.paziresh24.com/v1/search/tehran", headers=self.headers)
            self.expertises = [c[8:-1] for c in re.findall(r"/tehran/[a-zA-Z-]*/", json.dumps(response.json()))]
        except:
            print("--- Expertises Status Code == 500 ---\n--- Reading from log file ---")
            self.expertises = []
            try:
                with open('data_collection.log', 'r') as log_file:
                    lines = log_file.readlines()
                    for line in lines:
                        if "collected" in line:
                            self.expertises.append(line.strip().split('collected ')[1])
            except FileNotFoundError:
                pass
        self.cities = ['tehran', 'mashhad', 'shiraz', 'isfahan', 'tabriz', 'ahvaz', 'ilam', 'arak', 'ardabil', 'bandar-abbas', 'birjand', 'bushehr', 'karaj', 'orumieh', 'shahrekord', 'bojnurd', 'zanjan', 'semnan', 'zahedan', 'qazvin', 'qom', 'sanandaj', 'kerman', 'kermanshah', 'yasuj', 'gorgan', 'rasht', 'khorramabad', 'sari', 'hamedan', 'yazd']
        self.genders = ['&gender=male', '&gender=female']

        self.data = pd.DataFrame()

        logging.basicConfig(
            filename='data_collection.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            filemode='a'
        )

    def get_last_collected_strata(self) -> set:
        collected_strata = set()
        try:
            with open('data_collection.log', 'r') as log_file:
                lines = log_file.readlines()
                for line in lines:
                    if "collected" in line:
                        collected_strata.add(line.strip().split('collected ')[1])
        except FileNotFoundError:
            pass
        return collected_strata


    def get_strata(self, endpoint: str = "", sleep_multiplier: int = 1.5) -> pd.DataFrame:
        df = pd.DataFrame()
        status500 = 0
        for page_num in range(1, 26):
            time.sleep(sleep_multiplier * random() + 0.125)
            while True:
                try:
                    response = req.get(f"https://apigw.paziresh24.com/v1/search/{endpoint}&page={page_num}", headers=self.headers)
                    if response.status_code in [200, 500]:
                        break
                except Exception as e:
                    print(e)
                    time.sleep(sleep_multiplier * random() + 0.125)
                    pass

            if response.status_code != 500:
                result = response.json()['search']['result']
            else:
                print("--- Status Code == 500 ---")
                result = None

            if result:
                df_result = pd.DataFrame(result)
                new_df = pd.DataFrame()
                for col in ['id', 'display_name', 'name', 'gender', 'calculated_rate', 'rates_count', 'insurances', 'number_of_visits', 'expertise', 'display_expertise', 'display_address', 'waiting_time', 'badges', 'centers', 'actions', 'url', 'image']:
                    try:
                        new_df[col] = df_result[col]
                    except:
                        new_df[col] = None
                df = pd.concat([df, new_df], axis=0, ignore_index=True)
                print(f"-+- {time.strftime("%H:%M:%S")} got {endpoint} page {page_num}")
            elif status500 == 0:
                status500 += 1
                print(f"--- {time.strftime("%H:%M:%S")} {endpoint} page {page_num} is empty... moving on")
            else:
                print(f"--- {time.strftime("%H:%M:%S")} {endpoint} page {page_num} is empty... moving on")
                break
        return df

    def get_data(self, sleep_multiplier: int = 4) -> pd.DataFrame:
        collected_strata = self.get_last_collected_strata()

        for city in self.cities:
            for expertise in self.expertises:
                strata = f"{city}/{expertise}"
                if strata in collected_strata:
                    print(f"-*- {strata} already collected")
                    continue

                df = self.get_strata(strata + f"/?result_type=فقط+پزشکان")
                self.data = pd.concat([self.data, df], axis=0, ignore_index=True)
                
                if df.shape[0] == 500:
                    for gender in self.genders:
                        time.sleep(sleep_multiplier * random() + 0.125)
                        df = self.get_strata(strata + f"/?result_type=فقط+پزشکان{gender}")
                        self.data = pd.concat([self.data, df], axis=0, ignore_index=True)

                self.data.drop_duplicates(subset='id', inplace=True)
                self.data.to_csv('sample_running.csv')
                logging.info(f"collected {strata}")
        
        return self.data

if __name__ == "__main__":
    p = Paziresh24()
    tstamp0 = time.time()
    df = p.get_data()
    tstamp1 = time.time()
    print('total seconds:', tstamp1 - tstamp0)
