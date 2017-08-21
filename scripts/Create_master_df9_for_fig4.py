"""
Author: Janelle Becker
Date: 17-07-14

GOALS OF THIS SCRIPT:
    --Read in historical MTS's, get Table 9, clean, and concat to form a 
    Master Table 9 from the entire previous FY and this FY to date.
    

    # We want every file that ends "16" and any file ending in 17 up to this month
    # run them through the df9 cleaning process
    # concat 
    # return the master dataframe

    --Go back and use this master for the current FY/MO 
    

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
main_dir = "C:/Users/583902/Desktop/BAH1/_Treasury_DATA_Act/MTS"
data_dir = main_dir + "/data"
monthly_dir = data_dir + "/raw/monthly"
quarterly_dir = main_dir + "/raw/quarterly"
output_dir = data_dir + "/output"


os.chdir(monthly_dir) #change working directory to data in GA folder
os.listdir(os.getcwd()) #list out files in there 

"""|--------------------------------------------------------------------|"""
"""| INPUT CURRENT/PREV MONTH AND YEAR  HERE                            |"""
"""|--------------------------------------------------------------------|"""


current_mo = "05" # Use two digits
current_fy =    "17" # Use two digits

prev_mo = "04"
prev_fy = "16"


"""currently set for monthly in os.chdir below"""

""" Clear the output folder by moving any files to archived"""


"""|--------------------------------------------------------------------|"""
"""| Get list of filenames to use for this cleaning, concatting process |"""
"""|--------------------------------------------------------------------|"""

### We want every file that ends "16" and any file ending in 17 up to this month


# Get every file name ending with "17" AND "16" into a list
os.chdir(monthly_dir)
os.listdir(os.getcwd()) #list out files in there 

list_of_files_CFY = [filename for filename in os.listdir('.') if filename.endswith(current_fy + ".xls")]
list_sans_later_months = [item for item in list_of_files_CFY if int(item[3:5]) <= int(current_mo)]
list_of_files_PFY = [filename for filename in os.listdir('.') if filename.endswith(prev_fy + ".xls")]
list_both_fy = list_sans_later_months + list_of_files_PFY
list_both_fy

if prev_mo == "12":
    list_both_fy = list_of_files_PFY
else:
    list_both_fy = list_both_fy

list_both_fy   
   


"""|--------------------------------------------------------------------|"""
"""| RUN EACH FILE THROUGH CLEANING PROCESS & SAVE AS CSV               |"""
"""|--------------------------------------------------------------------|"""

for filename in list_both_fy:
    # Table 9 gives Source and Function for Receipts/Outlays
    path = monthly_dir + "/" + str(filename)
    whatiwant = {col: str for col in (0,3)}
    df9 = pd.read_excel(path, 
                       sheetname="Table 9", 
                       header=2, 
                       converters=whatiwant)
   
    # Remove whitespace in column names -------------------------------------------
    df9.columns.tolist() #oh it's a newline
    
    #Rename columns ---------------------------------------------------------------
    cols_df9 = df9.columns.tolist()
    rename_columns = [
            'source_func', 
            'amt',
            'fytd',
            'comp_per_pfy']
    for (oldcolname, replacement) in zip(cols_df9, rename_columns):
         df9.rename(columns={oldcolname : replacement}, inplace=True)
    df9.columns.tolist()    #check that it went right
    
    ### Add in year and month since it wasn't a part of this table anywhere but the title
    df9['fy'] = ""
    df9['fy'] = "20" + str(path[74:76])
    df9['month'] = ""
    df9['month'] = str(path[72:74])
    
    ### Create a column indicating if it's a receipt or an outlay -----------------
    
    # Create columns 
    df9['rec'] = False
    df9['outlay'] = False
    
        # Outlays index value
    bool_vector = df9.loc[:,'source_func'] == "Net Outlays"
    index_out = df9[bool_vector].index.tolist()
    index_out = index_out[0]
    
    # Make it true if receipt, true if outlay
    for i in range(0,index_out):
        df9['rec'][i] = True
    
    for i in range(index_out, len(df9)):
        df9['outlay'][i] = True
    
    # Drop the rows with just receipt/outlay in them and the final note ----------
    df9.drop(df9.index[[0, index_out]], inplace=True)
    df9 = df9[(df9['source_func'] != ". Note: Details may not add to totals due to rounding.")]
    df9.reset_index(drop=True, inplace=True)
    
    
    ### Strip whitespace from source_func column ----------------------------------
    df9['source_func'] = df9['source_func'].str.strip()
    df9['source_func'] = df9['source_func'].astype(str)
    
    # Unnest by creating a category variable
        #(instead of renaming, which I tried before) ------------------------------
    
    #Make new column based on old column 
    df9['source_func_parent'] = df9['source_func']
    
    # Find the index value for where this is true
    bool_vector = df9.loc[:,'source_func'] == "Employment and General Retirement"
    index_EGR = df9[bool_vector].index.tolist()
    index_EGR = index_EGR[0]
    
    bool_vector = df9.loc[:,'source_func'] == "Unemployment Insurance"
    index_UI = df9[bool_vector].index.tolist()
    index_UI = index_UI[0]
    
    bool_vector = (df9.loc[:,'source_func'] == "Other Retirement") | (df9.loc[:,'source_func'] == "OtherRetirement")
    index_OR = df9[bool_vector].index.tolist()
    index_OR = index_OR[0]
    
    index_SIRR = (index_EGR - 1)
    
    # Rename those cells
    df9['source_func_parent'][index_EGR] = "Social Insurance and Retirement Receipts"
    df9['source_func_parent'][index_UI] = "Social Insurance and Retirement Receipts"
    df9['source_func_parent'][index_OR] = "Social Insurance and Retirement Receipts"
    
    
    df9.drop(df9.index[index_SIRR], inplace=True)
    df9.reset_index(drop=True, inplace=True)
    
    #Convert numbers from str to int ----------------------------------------------
    
    # remove all commas
    df9['amt'] = df9['amt'].str.replace(',', '')
    df9['fytd'] = df9['fytd'].str.replace(',', '')
    df9['comp_per_pfy'] = df9['comp_per_pfy'].str.replace(',', '')
    
    # (**) is a value below $500,000 and we dont know what it is, so.... zero
    df9['amt'] = df9['amt'].str.replace('\(\*\*\)', '0') #* is a special character in regex, you have to escape it: regex=False gave me error
    df9['fytd'] = df9['fytd'].str.replace('\(\*\*\)', '0')
    df9['comp_per_pfy'] = df9['comp_per_pfy'].str.replace('\(\*\*\)', '0')
    
    # make an integer
    df9['amt'] = df9['amt'].astype(float)
    df9['fytd'] = df9['fytd'].astype(float)
    df9['comp_per_pfy'] = df9['comp_per_pfy'].astype(float)
    
    
    ### Add in S/D so we can simply use Table 9 instead of merge 
        # to power the cover figure -----------------------------------------------
    
    
    index_tot_rec = df9[(df9.loc[:, 'source_func']=="Total") & (df9.loc[:, 'rec']==True)].index.tolist()[0]
    index_tot_out = df9[(df9.loc[:, 'source_func']=="Total") & (df9.loc[:, 'outlay']==True)].index.tolist()[0]
    
    deficit_mo = -1*(df9['amt'][index_tot_rec] - df9['amt'][index_tot_out])
    deficit_fytd = -1*(df9['fytd'][index_tot_rec] - df9['fytd'][index_tot_out])
    
    
    temp = pd.DataFrame( [["deficit for the month", deficit_mo, 0, 0, "20" + str(path[74:76]), str(path[72:74]),False,False,"Deficit"],
                         ["deficit fytd", 0, deficit_fytd,0,"20" + str(path[74:76]),str(path[72:74]),False,False,"Deficit"]],
        columns = ['source_func', 'amt', 'fytd', 'comp_per_pfy', 
                   'fy', 'month', 'rec', 'outlay','source_func_parent'])
    
    
    
    df9 = pd.concat([df9, temp], axis=0)
    df9.reset_index(drop=True, inplace=True)
    
    title = filename[:-4]
   
    ### Write to CSV --------------------------------------------------------------
    df9.to_csv(output_dir + "/df9_from_" + str(title) + ".csv", index=False, header=True)

#Done? holy moly that finally worked.


"""|--------------------------------------------------------------------|"""
"""| Read in df9's and concat to form master df9 for current month      |"""
"""|--------------------------------------------------------------------|"""

os.chdir(output_dir) #change working directory to data in GA folder
os.listdir(os.getcwd()) #list out files in there 

#Put all filepaths by report into a list 
df9_filename_list = [filename for filename in os.listdir('.')]


list_of_dfs = [pd.read_csv(x, index_col=0, encoding = 'latin1') for x in df9_filename_list]

 # For longer datasets, this can hit performance hard, so be efficient with RAM/memory
 # and do 2 at a time then delete 


df9_master = list_of_dfs[0]
starting_index = len(list_of_dfs)-1
for i in range(starting_index, 0, -1):
    df9_master = pd.concat([df9_master, list_of_dfs[i]], ignore_index = True)
    del list_of_dfs[i]




### Write to CSV --------------------------------------------------------------
df9_master.to_csv(output_dir + "/master_df9" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)








