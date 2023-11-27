#K-means算法
import pandas as pd
from sklearn.cluster import KMeans
old_df = pd.read_csv("SIN_checkin.csv", encoding= 'unicode_escape')

old_df['avg_Latitude'] = old_df.groupby('POI_id')['Latitude'].transform('mean')
old_df['avg_Longitude'] = old_df.groupby('POI_id')['Longitude'].transform('mean')
df = old_df[["avg_Latitude", "avg_Longitude"]]
y = KMeans(n_clusters=10).fit_predict(df)
old_df["clusters"] = y
old_df = old_df.sort_values('POI_id')
old_df.to_csv("SIN_checkin_clusters.csv", index=False)