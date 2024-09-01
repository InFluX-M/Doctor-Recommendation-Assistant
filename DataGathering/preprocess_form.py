import pandas as pd
import re

def fix_punctuation_spacing(text):
    text = re.sub(r'([.,?!،])', r' \1 ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def preprocess_form():
    f = open("results.txt", "a")

    df = pd.read_csv('FormData.csv')
    print(df.columns)
    for index, row in df.iterrows():
        if index < 53:
            continue
        data = row['متن‌تون رو اینجا بنویسید']
        data = data.replace('\u200C', ' ')
        data = fix_punctuation_spacing(data)
        labels = ""
        datas = data.split(' ')
        for d in datas:
            print(data)
            label = input(d + ': ')
            labels += label + ' '
        labels = labels.strip()
        f.write(data + '\n' + labels + '\n')
        print(labels)

def preprocess_result():
    r = open("final_results.txt", "a")
    f = open("results.txt", "r")
    lines = f.readlines()
    for i in range(0, len(lines), 2):
        data1 = lines[i].strip()
        data2 = lines[i+1].strip()
        data2 = data2.replace(' ', ',')
        r.write(data1 + '\n' + data2 + '\n')
        print(data1)
        print(data2)
        
preprocess_result()