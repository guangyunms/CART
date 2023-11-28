import pandas as pd
from sklearn.preprocessing import LabelEncoder  

Label_encoder = LabelEncoder()
data = pd.read_csv('SIN_checkin_clusters.csv')
data['Item_id'] = data['POI_id']
data['POI_Type'] = data['POI_Type'].map({'Independent': 0, 'Combined': 1})
data['L2_Category_name'] = Label_encoder.fit_transform(data['Category'])
data['L1_Category_name'] = Label_encoder.fit_transform(data['Combined_Category'])
data['new_time'] = data['hour']
data.to_csv('SIN_checkin_clusters_re.csv')
