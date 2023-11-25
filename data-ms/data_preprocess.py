import pandas as pd
import json
from sklearn.preprocessing import LabelEncoder  

# 将四个csv合并到一起
# file_list = ["CAL_checkin.csv", "CHA_checkin.csv", "PHO_checkin.csv", "SIN_checkin.csv"]
# dfs = [pd.read_csv(i) for i in file_list]
# for j in dfs:
#     print(j.shape)
# df = pd.concat(dfs,ignore_index=True)
# print(df.shape)

df = pd.read_csv('SIN_checkin.csv')

# 第一个数据处理
# 将Category字段中的字符串转换为数字
Label_encoder = LabelEncoder()
df['Category_encoded'] = Label_encoder.fit_transform(df['Category'])


# 将'Combined_Category', 'Category', 'Category_encoded'三列提取出来并去重
df_2 = df.loc[:,['Combined_Category', 'Category', 'Category_encoded']]
print(df_2)
df_3 = df_2.drop_duplicates()
print(df_3)

# 根据Combined_Category字段分组，并聚合每一组的Category_encoded合并为list
grouped = df_3.groupby('Combined_Category')['Category_encoded'].agg(list)  
# 将结果转换为字典  
dictionary = grouped.to_dict()  


print(dictionary)
with open('data-SIN.json', 'w') as f:
    json.dump(dictionary, f)
    print('json文件生成完毕')


# 第二个数据处理
df['Item_id'] = df['POI_id']
df['POI_Type'] = df['POI_Type'].map({'Independent': 0, 'Combined': 1})
df['L2_Category_name'] = df['Category_encoded']
df_4 = df.loc[:,['Item_id', 'POI_Type', 'L2_Category_name', 'stars', 'clusters']]
df_4 = df_4.drop_duplicates()
print(df_4)

df_4.to_csv('dict-SIN.csv')