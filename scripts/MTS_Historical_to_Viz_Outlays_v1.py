"""
Author: Janelle Becker
Original Date: 17-08-07

GOALS OF THIS SCRIPT:
    --Read in historical MTS data table (outlays)
    --Get the data in a dataframe format that is ready for data visualization 
        --Ideally tool-agnostic, but for now, assuming LONG dataset 
    
    
    # Create separate dataframe of the following by splitting into 3 df's
    (1) numbers
    (2) percent of outlays
    (3) percent of gdp
    
    
    
    --v2 changes:



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
hist_dir = data_dir + "/Historical_Tables/GPO_Historical_Tables"
output_dir = data_dir + "/output/historical_output"


os.chdir(hist_dir) #change working directory to data in GA folder
os.listdir(os.getcwd()) #list out files in there 

"""|--------------------------------------------------------------------|"""
"""| Random Technical Notes                                             |"""
"""|--------------------------------------------------------------------|"""

"""   
FILE NAMES
for some reason these file names are off by one. Table 3.1 is 
#called 4-1 :(

# Table 3.1—OUTLAYS BY SUPERFUNCTION AND FUNCTION: 1940–2021
    # numbers are in millions (from excel)
    # (*) * 0.05 percent or less.
    # (−*) i guess negative less than .05 percent?

FISCAL YEAR 
The first fiscal year for the U.S. Government started Jan. 1, 1789. Congress 
changed the beginning of the fiscal year from Jan. 1 to Jul. 1 in 1842, and 
finally from Jul. 1 to Oct. 1 in 1977 where it remains today.


# Some functions started at different times, e.g. Medicare or General Science 
    I converted these "...." to zeroes.

"""



"""|--------------------------------------------------------------------|"""
"""| Bring in the data                                                  |"""
"""|--------------------------------------------------------------------|"""


# Table 3.1—OUTLAYS BY SUPERFUNCTION AND FUNCTION: 1940–2021

# numbers are in millions (from excel)
# (*) * 0.05 percent or less.
# (−*) i guess negative less than .05 percent?

path = hist_dir + "/BUDGET-2017-TAB-4-1.xls"
whatiwant = {col: str for col in (0,83)} #got 84 from excel...smart way to do this if data were huge???
df = pd.read_excel(path, 
                   sheetname="Table", 
                   header=1,
                   skiprows = [2, 57],
                   converters=whatiwant)

"""|--------------------------------------------------------------------|"""
"""| Wrangle in the data                                                |"""
"""|--------------------------------------------------------------------|"""


#Check out the column names 
cols_df = df.columns.tolist()


#Rename columns ----------------------------------------------------------------
cols_to_change = cols_df[1:]
cols_new_names = ["outlays_M_" + str(i) for i in cols_to_change]

# Add in the superfunction column name back to the list
cols_new_names = ['Superfunction_and_Function'] + cols_new_names

for (oldcolname, replacement) in zip(cols_df, cols_new_names):
     df.rename(columns={oldcolname : replacement}, inplace=True)


#Still have a few i want to rename and I don't feel like making new lists
df.rename(columns= {"outlays_M_2016 estimate" : "outlays_M_2016_estimate"}, inplace=True)
df.rename(columns= {"outlays_M_2017 estimate" : "outlays_M_2017_estimate"}, inplace=True)
df.rename(columns= {"outlays_M_2018 estimate" : "outlays_M_2018_estimate"}, inplace=True)
df.rename(columns= {"outlays_M_2019 estimate" : "outlays_M_2019_estimate"}, inplace=True)
df.rename(columns= {"outlays_M_2020 estimate" : "outlays_M_2020_estimate"}, inplace=True)
df.rename(columns= {"outlays_M_2021 estimate" : "outlays_M_2021_estimate"}, inplace=True)

#check that it went right
cols_df = df.columns.tolist()    
cols_df

"""|--------------------------------------------------------------------|"""
"""| Create 3 dataframes: $, % of outlays, % of GDP                     |"""
"""|--------------------------------------------------------------------|"""
# I want to create a separate dataframe for the "As a percent of outlays" numbers

#Find the line that says "As percentages of outlays:" and its index
index_pct_OL_header = df[(df.loc[:, 'Superfunction_and_Function']=="As percentages of outlays: ")].index.tolist()[0]
index_pct_GDP_header = df[(df.loc[:, 'Superfunction_and_Function']=="As percentages of GDP: ")].index.tolist()[0]

# Rows 0 to index_pct_OL_header is what I want
# Rows index_pct_OL_header to index_pct_GDP_header is % of outlays
# Rows  index_pct_GDP_header to the end is % of GDP

df1 = df[:] #make a copy instead of renaming the actual dataframe
df = df1[:index_pct_OL_header]
df_pct_OL = df1[index_pct_OL_header:index_pct_GDP_header]
df_pct_GDP = df1[index_pct_GDP_header:]


"""|--------------------------------------------------------------------|"""
"""| Wrangle the data to get just functions & values                    |"""
"""|--------------------------------------------------------------------|"""
# I only want the FUNCTIONS, and there are a lot of other lines, e.g. on- and off-budget numbers

### Drop row if it is offering on-budget or off-budget numbers -------------------

# make sure it's a string and stripped/trimmed
df['Superfunction_and_Function'] = df['Superfunction_and_Function'].str.strip()
df['Superfunction_and_Function'] = df['Superfunction_and_Function'].astype(str)

#Keep the rows where the function does not include the word "budget"
df = df[~df['Superfunction_and_Function'].str.contains('budget')]
df.reset_index(drop=True, inplace=True)


### Find all ".........." and replace with NaN for the whole dataframe----------------
#When no values are available (e.g. Medicare in 1950) they used ".........."
df = df.replace("..........", 0)


### Ensure all numbers are typed as floats or integers---------------------------
# For some reason, the 2021 estimate column isn't a number?
cols_df
type(df['outlays_M_2020_estimate'][0]) # numpy.float64
type(df['outlays_M_2021_estimate'][0]) # STR ??


df['outlays_M_2021_estimate'] = df['outlays_M_2021_estimate'].astype(float)
type(df['outlays_M_2021_estimate'][0]) # numpy.float64

    
    


















































