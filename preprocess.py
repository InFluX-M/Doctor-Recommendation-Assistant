import pandas as pd
import sqlite3
import os

class Doctor:
    def __init__(self, dataframe:pd.DataFrame) -> None:
        self.df = dataframe

    def correct_gender(self, sql_script_path: str) -> pd.DataFrame:
        # get names dataset from sql script
        try:
            os.remove('data/persian_names.db')
        except FileNotFoundError:
            pass
        conn = sqlite3.connect('data/persian_names.db')
        cursor = conn.cursor()
        with open(sql_script_path, 'r', encoding='utf-8') as file:
            conn.executescript(file.read())
            conn.commit()
        cursor.execute("SELECT name, sex FROM names")
        rows = cursor.fetchall()
        conn.close()
        names = pd.DataFrame(rows, columns = ['name', 'gender'])
        os.remove('data/persian_names.db')

        # cleaning names dataset
        names['gender'] = names['gender'].apply(lambda x: 1 if x == 'پسر' else 2)
        names = names.groupby('name').mean().reset_index()
        names.loc[names['gender'] == 1.5, 'gender'] = None
        names.dropna(inplace=True)

        # correct the genders
        api_gender = self.df['gender'].copy().apply(lambda x: x if x in [1, 2] else None)
        self.df.drop('gender', axis=1, inplace=True)
        self.df['name'].loc[self.df['name'].isna()] = self.df['display_name'].loc[self.df['name'].isna()].str.split().str[0] # fill missing names with display_name's first word
        self.df = pd.merge(self.df, names, how='left', on='name')
        self.df = self.df[
            ['id', 'display_name', 'name', 'gender', 'calculated_rate', 'rates_count', 'insurances', 'number_of_visits', 'expertise', 'display_expertise', 'display_address', 'waiting_time', 'badges', 'centers', 'actions', 'url', 'image']
        ] # reorder columns
        for fname in [' سیده', 'سیده‌', 'سادات']:
            self.df['gender'].loc[(self.df['name'].str.contains(fname)) & (self.df['gender'].isna())] = 2
        self.df['gender'].loc[(self.df['name'].str.contains("سید")) & (self.df['gender'].isna())] = 1
        self.df['gender'].loc[(self.df['gender'].isna())] = api_gender.loc[(self.df['gender'].isna())]
        return self.df
        

if __name__ == "__main__":
    doctor = Doctor(pd.read_csv("data/doctors.csv"))
    doctor.correct_gender("data/names.sql")
