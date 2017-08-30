"""
Author: Janelle Becker
GOALS OF THIS SCRIPT:
    --Merge MTS receipt/outlay data with "model" data to have a [-6,6] t value
        for each source/function and then calculate the curve with that
    --Define the rank myself so it reflects what I want

"""
### Import stuff --------------------------------------------------------------
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import numpy as np
import json
import urllib
from pandas.io.json import json_normalize
import os
import xlrd

start = time.time()

### SET UP THE DIRECTORIES ----------------------------------------------------
main_dir = "C:/Users/583902/Desktop/BAH1/_Treasury_DATA_Act/Sprint14"
sankey_dir = main_dir + "/2_MTS_Github/tableau visualizations/_Sankey_Cover_Figure_Revamp"

path = sankey_dir + "/fig0_cover_0517_modified_v6_for_sankey_v1.5_post_johnsandoval.xlsx"
df_outlays = pd.read_excel(path, sheetname = "data_outlays")
df_receipts = pd.read_excel(path, sheetname = "data_receipts")
model =  pd.read_excel(path, sheetname = "model")

del model['Path']
del model['MinMax']


df_outlays_new = pd.merge(df_outlays, model, how="inner", on="Link")
df_receipts_new = pd.merge(df_receipts, model, how="inner", on="Link")


"""
#this gives the same messed up results as Sandoval's output file - went in with 
# 12 functions, came out with 8... 

df = pd.concat([df_receipts_new, df_outlays_new], axis=1)
df = df.loc[:,~df.columns.duplicated()]
del df['Link']
df.sort_values(by='t')

df.drop_duplicates()
"""

del df_outlays_new['Link']
del df_receipts_new['Link']

df_outlays_new = df_outlays_new.drop_duplicates()
df_receipts_new = df_receipts_new.drop_duplicates() #note this is 392 rows, same as Sandoval output where it cut off a few functions

df_outlays_new.sort_values(by='t')
df_receipts_new.sort_values(by='t')


### RANK ---------------------------------------------------------------------
sum_rec = df_receipts['Stage1_Source_Amount'].sum()
#REmove deficit
index_def = df_receipts[(df_receipts.loc[:, 'Stage2_Receipt_Type']=="Deficit")].index.tolist()[0]
deficit = df_receipts['Stage1_Source_Amount'][index_def]

sum_receipts = sum_rec - deficit
sum_outlays = df_outlays['Stage3_Outlay_Amount'].sum()


df_o = df_outlays_new
df_r = df_receipts_new
del df_outlays_new
del df_receipts_new


df_r['pct_of_receipts'] = df_r['Stage1_Source_Amount']/sum_receipts
df_o['pct_of_outlays'] = df_o['Stage3_Outlay_Amount']/sum_outlays

df_r.sort_values(by='t', inplace=True)
df_o.sort_values(by='t', inplace=True)

df_r.reset_index(drop=True, inplace=True)
df_o.reset_index(drop=True, inplace=True)

    # RECEIPTS 

# Create rank from true receipt values, thus pillar 2
df_r['pillar2_rank_wt'] = df_r['Stage1_Source_Amount'].rank(axis=0, ascending=True) #no idea what these are
df_r['pillar2_rank']= df_r.groupby(['t'])['Stage1_Source_Amount'].rank(ascending=False) #1-n

# Top half --> make it go up 
# midpoint --> straight 
# Bottom half --> make it go down

num_rec_grps = df_r['pillar2_rank'].max()

# Straight Rank ---- this doesn't make sense actually
    # because 1 becomes 1.05 but 2 becomes 2.01
#df_r['pillar1_rank'] = ""
#
#for i in range(len(df_r)):
#    if df_r['pillar2_rank'][i] < num_rec_grps/2:
#        df_r['pillar1_rank'][i] = df_r['pillar2_rank'][i]*1.05
#    elif df_r['pillar2_rank'][i] > num_rec_grps/2:
#        df_r['pillar1_rank'][i] = df_r['pillar2_rank'][i]*0.95
#    else:
#        df_r['pillar1_rank'][i] = df_r['pillar2_rank'][i]
#        
    
# Weighted Rank
df_r['pillar1_rank_wt'] = ""

for i in range(len(df_r)):
    if df_r['pillar2_rank'][i] < num_rec_grps/2:
        df_r['pillar1_rank_wt'][i] = df_r['pillar2_rank_wt'][i]*1.05
    elif df_r['pillar2_rank'][i] > num_rec_grps/2:
        df_r['pillar1_rank_wt'][i] = df_r['pillar2_rank_wt'][i]*0.95
    else:
        df_r['pillar1_rank_wt'][i] = df_r['pillar2_rank_wt'][i]

df_r['pillar1_rank_wt'] = df_r['pillar1_rank_wt'].astype(float)
df_r['pillar1_rank'] = df_r['pillar1_rank'].astype(float)
















### SIGMOID AND CURVE  -----------------------------------------------------------------

    # RECEIPTS ONLY

df_r['sigmoid'] = ""

for i in range(len(df_r)):    
    df_r['sigmoid'][i] = 1/(1+np.exp(1)**-(df_r['t'][i]))


df_r['curve'] = ""

for i in range(len(df_r)):    
    df_r['curve'][i] = df_r['pillar1_rank_wt'][i] + ((df_r['pillar2_rank_wt'][i] - df_r['pillar1_rank_wt'][i])*df_r['sigmoid'][i])




df_r['sigmoid'] = df_r['sigmoid'].astype(float)
df_r['curve'] = df_r['curve'].astype(float)





df_r.to_csv(sankey_dir + "/fig0_cover_0517_modified_v6_for_sankey_v1.5_post_johnsandoval+pythonmod_170828.csv", index=False, header=True)









