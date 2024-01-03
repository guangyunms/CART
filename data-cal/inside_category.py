#create poi
import pandas as pd
import json
from sklearn.preprocessing import LabelEncoder

poi_dict = dict()
star_list = dict()
# df = pd.read_csv('new_transE_3.csv', usecols=['Item_id','Location_id','POI_Type','POI','stars','L2_Category_name'])

df = pd.read_csv('new_transE_3.csv')
# Label_encoder = LabelEncoder()
# df['L2_Category_name'] = Label_encoder.fit_transform(df['Category'])
# df['POI'] = df['POI_Type']
# df['POI_Type'] = df['POI_Type'].map({'Independent': 0, 'Combined': 1})
# df['Item_id'] = df['POI_id']
df = df.loc[:, ['Item_id','Location_id','POI_Type','POI','stars','L2_Category_name']]

# 生成inside_category.csv
df_2 = df[df['POI_Type'] == 1]
df_2 = df_2.loc[:, ['Location_id','Item_id','POI_Type','L2_Category_name','POI']]
df_2 = df_2.drop_duplicates()
df_2.to_csv('inside_category.csv')