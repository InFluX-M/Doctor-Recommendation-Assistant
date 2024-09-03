import pandas as pd
import sqlite3
import os
import ast
import re
import jdatetime
from datetime import datetime

class Doctor:
    def __init__(self, dataframe:pd.DataFrame) -> None:
        self.dataframe = dataframe

    def correct_gender(self, sql_script_path: str) -> None:
        if not os.path.exists("temp"):
            os.makedirs("temp")

        # get names dataset from sql script
        try:
            os.remove('temp/persian_names.db')
        except FileNotFoundError:
            pass
        conn = sqlite3.connect('temp/persian_names.db')
        cursor = conn.cursor()
        with open(sql_script_path, 'r', encoding='utf-8') as file:
            conn.executescript(file.read())
            conn.commit()
        cursor.execute("SELECT name, sex FROM names")
        rows = cursor.fetchall()
        conn.close()
        names = pd.DataFrame(rows, columns = ['name', 'gender'])
        os.remove('temp/persian_names.db')

        # cleaning names dataset
        names['gender'] = names['gender'].apply(lambda x: 1 if x == 'پسر' else 2)
        names = names.groupby('name').mean().reset_index()
        names.loc[names['gender'] == 1.5, 'gender'] = None
        names.dropna(inplace=True)

        # correct the genders
        api_gender = self.dataframe['gender'].copy().apply(lambda x: x if x in [1, 2] else None)
        self.dataframe.drop('gender', axis=1, inplace=True)
        self.dataframe['name'].loc[self.dataframe['name'].isna()] = self.dataframe['display_name'].loc[self.dataframe['name'].isna()].str.split().str[0] # fill missing names with display_name's first word
        self.dataframe = pd.merge(self.dataframe, names, how='left', on='name')
        self.dataframe = self.dataframe[
            ['id', 'display_name', 'name', 'gender', 'calculated_rate', 'rates_count', 'insurances', 'number_of_visits', 'expertise', 'display_expertise', 'display_address', 'waiting_time', 'badges', 'centers', 'actions', 'url', 'image']
        ] # reorder columns
        for fname in [' سیده', 'سیده‌', 'سادات']:
            self.dataframe['gender'].loc[(self.dataframe['name'].str.contains(fname)) & (self.dataframe['gender'].isna())] = 2
        self.dataframe['gender'].loc[(self.dataframe['name'].str == "سیده") & (self.dataframe['gender'].isna())] = 2

        self.dataframe['gender'].loc[(self.dataframe['name'].str.contains("سید")) & (self.dataframe['gender'].isna())] = 1
        self.dataframe['gender'].loc[(self.dataframe['gender'].isna())] = api_gender.loc[(self.dataframe['gender'].isna())]
        def gender_to_text(x):
            if x == 1:
                return 'مرد'
            elif x == 2:
                return 'زن'
            else:
                return None
        self.dataframe['gender'] = self.dataframe['gender'].apply(gender_to_text)
        return
    
    def convert_str_to_list(self) -> None:
        for col in ['insurances', 'expertise', 'badges', 'centers', 'actions']:
            self.dataframe[col] = self.dataframe[col].apply(lambda x: ast.literal_eval(x))
        return
        
    def process_badges(self) -> None:
        self.dataframe['badges'] = self.dataframe['badges'].apply(
            lambda x: [badge['title'] for badge in x if "فعال" not in badge['title']]
        )
        return
    
    def process_actions(self) -> None:

        def online_visit(actions):
            for action in actions:
                if action['title'] == 'ویزیت آنلاین':
                    return True
            return False
        def first_available_appointment(actions):
            for action in actions:
                if 'اولین نوبت' in action['top_title']:
                    return re.findall(r'<b>.*</b>', action['top_title'])[0][3:-4]
            return None
        
        self.dataframe['online_visit'] = self.dataframe['actions'].apply(online_visit)
        self.dataframe['first_available_appointment'] = self.dataframe['actions'].apply(first_available_appointment)
        self.dataframe.drop('actions', axis=1, inplace=True)

        return
    
    def process_centers(self) -> None:
        def prune(centers):
            center_type = {
                1: "مطب",
                2: "بیمارستان/درمانگاه",
                3: "کلینیک تخصصی"
            }
            result = []
            for center in centers.copy():
                if center['address'] == None and center['display_number'] == None:
                    continue
                elif center['name'] == 'ویزیت آنلاین پذیرش24':
                    continue
                else:
                    for key in ['id', 'user_center_id', 'server_id', 'active_booking', 'map']:
                        center.pop(key)
                    try:
                        center['center_type'] = center_type[center['center_type']]
                    except KeyError:
                        center['center_type'] = "متفرقه"
                center['address'] = f"{center.pop('province_name')}، {center.pop('city_name')}، {center.pop('address')}"
                result.append(center)
            return result
        
        self.dataframe['centers'] = self.dataframe['centers'].apply(prune)
        return
    
    @classmethod
    def convert_text_to_gregorian(cls, text: str) -> datetime:
        if text == None:
            return None
        months = {
            'فروردین': 1,
            'اردیبهشت': 2,
            'خرداد': 3,
            'تیر': 4,
            'مرداد': 5,
            'شهریور': 6,
            'مهر': 7,
            'آبان': 8,
            'آذر': 9,
            'دی': 10,
            'بهمن': 11,
            'اسفند': 12
        }
        text = text.split(' ')
        if text[0] in ['امروز', 'کمتر']:
            date = jdatetime.date.today()
        elif text[0] == 'فردا':
            date = jdatetime.date.today() + jdatetime.timedelta(days=1)
        else:
            day = text[0]
            month = months.get(text[1])
            year = jdatetime.date.today().year
            if jdatetime.date.today().month > month:
                year += 1
            date = jdatetime.date(year, month, int(day))
        gregorian_datetime = date.togregorian()
        return str(gregorian_datetime)
    
    def convert_first_available_appointment(self) -> None:
        self.dataframe['first_available_appointment'] = self.dataframe['first_available_appointment'].apply(self.convert_text_to_gregorian)
        return
    
    def process(self, sql_script_path: str) -> pd.DataFrame:
        self.correct_gender(sql_script_path)
        self.convert_str_to_list()
        self.process_badges()
        self.process_actions()
        self.process_centers()
        self.convert_first_available_appointment()
        self.dataframe.drop(columns=['name', 'url'], inplace=True)
        return self.dataframe
    
if __name__ == "__main__":
    doctor = Doctor(pd.read_csv("data/doctors.csv"))
    df = doctor.process("data/names.sql")
    df.to_json("data/doctors.json", orient='records', force_ascii=False)