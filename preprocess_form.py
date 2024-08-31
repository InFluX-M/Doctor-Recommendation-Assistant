import pandas as pd
import numpy as np
import re

def fix_punctuation_spacing(text):
    # افزودن فاصله بعد از علائم نگارشی
    text = re.sub(r'([.,?!])', r' \1 ', text)
    
    # حذف فاصله‌های اضافی که ممکن است به دلیل اضافه کردن فاصله‌ها ایجاد شده باشند
    text = re.sub(r'\s+', ' ', text)
    
    # حذف فاصله‌های ناخواسته در ابتدای و انتهای جمله
    text = text.strip()
    
    return text


df = pd.read_csv('FormData.csv')
print(df.columns)
for index, row in df.iterrows():
    data = row['متن‌تون رو اینجا بنویسید']

    data = data.replace('\u200C', ' ')
    data = fix_punctuation_spacing(data)
    print(data)
    labels = ""
    datas = data.split(' ')
    for d in datas:
        label = input(d + ': ')
        labels += label + ' '
    labels = labels.strip()
    print(labels)
    break