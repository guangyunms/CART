#create poi
import pandas as pd
import json
from sklearn.preprocessing import LabelEncoder

poi_dict = dict()
star_list = dict()
# df = pd.read_csv('new_transE_3.csv', usecols=['Item_id','Location_id','POI_Type','POI','stars','L2_Category_name'])

df = pd.read_csv('SIN_checkin.csv')
Label_encoder = LabelEncoder()
df['L2_Category_name'] = Label_encoder.fit_transform(df['Category'])
df['POI'] = df['POI_Type']
df['POI_Type'] = df['POI_Type'].map({'Independent': 0, 'Combined': 1})
df['Item_id'] = df['POI_id']
df = df.loc[:, ['Item_id','Location_id','POI_Type','POI','stars','L2_Category_name']]

df_2 = df[df['POI_Type'] == 1]
df_2 = df_2.loc[:, ['Location_id','Item_id','POI_Type','L2_Category_name','POI']]
df_2 = df_2.drop_duplicates()
df_2.to_csv('inside_category_SIN.csv')


# for index, row in df.iterrows():
#     if str(int(row['Item_id'])) not in poi_dict:
#         row_dict = dict()
#         row_dict['stars'] = [row['stars']]
#         row_dict['Location_id'] = [int(row['Location_id'])]
#         row_dict['POI'] = row['POI']
#         row_dict['POI_Type'] = int(row['POI_Type'])
#         row_dict['L2_Category_name'] = [int(row['L2_Category_name'])]
#         poi_dict[str(int(row['Item_id']))] = row_dict
#     else:
#         if int(row['Location_id']) not in poi_dict[str(int(row['Item_id']))]['Location_id']:
#             poi_dict[str(row['Item_id'])]['Location_id'].append(row['Location_id'])
#             poi_dict[str(row['Item_id'])]['stars'].append(row['stars'])
#             poi_dict[str(row['Item_id'])]['L2_Category_name'].append(row['L2_Category_name'])


# with open('poi.json', 'w') as json_file:
#     json.dump(poi_dict, json_file)