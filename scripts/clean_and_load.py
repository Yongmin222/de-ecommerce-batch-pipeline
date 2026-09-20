import pandas as pd
from sqlalchemy import create_engine

# 1. 원본 CSV 읽기
df = pd.read_csv('/opt/airflow/data/2019-Oct.csv')

# 2. 정제
df['event_time'] = pd.to_datetime(df['event_time'])
df['brand'] = df['brand'].fillna('Unknown')
df['has_category'] = df['category_code'].notna()
df = df.dropna(subset=['user_session'])
df = df[df['price'] >= 0]

print(f"정제 완료: {df.shape[0]}행")

# 3. MySQL에 적재
engine = create_engine('mysql+pymysql://root:de1234!@mysql-de:3306/de_portfolio')
df.to_sql('events', con=engine, if_exists='replace', index=False, chunksize=10000)

print("적재 완료")
