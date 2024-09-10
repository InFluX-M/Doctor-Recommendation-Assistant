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
        
    def process_waiting_time(self) -> None:
        self.dataframe['waiting_time'] = self.dataframe['waiting_time'].replace({
            'کمتر از نیم ساعت': 0,
            'کمتر از یک ساعت': 1,
            'بیشتر از یک ساعت': 2,
            'کمتر از دو ساعت': 3,
            'بیشتر از دو ساعت': 4
        })
        self.dataframe['waiting_time'] = self.dataframe['waiting_time'].fillna(5)
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
                # center['address'] = f"{center.pop('province_name')}، {center.pop('city_name')}، {center.pop('address')}"
                result.append(center)
            return result
        
        self.dataframe['centers'] = self.dataframe['centers'].apply(prune)
        return
    
    @classmethod
    def convert_text_to_gregorian(cls, text: str) -> str | None:
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
    
    def convert_first_available_appointment(self) -> None:
        self.dataframe['first_available_appointment'] = self.dataframe['first_available_appointment'].apply(self.convert_text_to_gregorian)
        return
    
    def process(self, sql_script_path: str) -> pd.DataFrame:
        self.dataframe.drop_duplicates(subset='url', keep='first', inplace=True, ignore_index=True)
        self.correct_gender(sql_script_path)
        self.convert_str_to_list()
        self.process_waiting_time()
        self.process_badges()
        self.process_actions()
        self.process_centers()
        self.convert_first_available_appointment()
        self.dataframe.drop(columns=['id', 'name', 'display_address', 'image'], inplace=True)
        return self.dataframe
    
if __name__ == "__main__":
    doctor = Doctor(pd.read_csv("data/doctors.csv"))
    df = doctor.process("data/names.sql")
    df.reset_index().to_json("data/doctors.json", orient='records', force_ascii=False)
    df.to_csv("data/processed_doctors.csv", index=False)