"""
Author: Janelle Becker
Date: 17-07-12, 13, 17, 27

GOALS OF THIS SCRIPT:
    --Read in an MTS
    --Only need Tables 1, 7, 9
    --Get the data in each table in a dataframe format that is ready for data visualization 
        --Ideally tool-agnostic, but for now, assuming LONG dataset 
    
    --v2 changes:
        -realized table 7 couldn't power fig 3 cause it lacked previos FY
        --> need to use concat'ed Table 9 for both figs 3 and 4, i guess
        -deleted all the Table 7 cleaning/wrangling
        
    --v3 changes:
        --convert numbers from millions/billions scaled to absolute values so tableau can format

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

###############################################################################
###############################################################################
###############################################################################
"""|--------------------------------------------------------------------|"""
"""| INPUT CURRENT/PREV MONTH AND YEAR  HERE                            |"""
"""|--------------------------------------------------------------------|"""


current_mo = "05" # Use two digits
current_fy =    "17" # Use two digits

prev_mo = "04"
prev_fy = "16"


"""currently set for monthly in os.chdir below"""

""" Clear the output folder by moving any files to archived"""

###############################################################################
###############################################################################
###############################################################################




# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#

"""|--------------------------------------------------------------------|"""
"""|--STEP 1: MAKE df's TO DRIVE THE VISUALIZATIONS: ??? --> Cover Fig  |"""
"""|--------------------------------------------------------------------|"""

# Cover Figure requires Table 9 ==> read that in and clean it up 

"""|--------------------------------------------------------------------|"""
"""| READ IN THE DATA - Table 9 (Sources/Functions)                     |"""
"""|--------------------------------------------------------------------|"""
# Table 9 gives Source and Function for Receipts/Outlays
path = monthly_dir + "/mts0517.xls"
whatiwant = {col: str for col in (0,3)}
df9 = pd.read_excel(path, 
                   sheetname="Table 9", 
                   header=2, 
                   converters=whatiwant)


"""|--------------------------------------------------------------------|"""
"""| WRANGLE THE DATA - Table 9                                         |"""
"""|--------------------------------------------------------------------|"""

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

# Figure out the indices for where it's labeled receipt/outlay 
    # Receipt's index value should be zero 
#bool_vector = df9.loc[:,'source_func'] == "Receipts"
#index_rec = df9[bool_vector].index.tolist()
#index_rec = index_rec[0]


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

bool_vector = df9.loc[:,'source_func'] == "Other Retirement"
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



### Create dataframe for the figure ------------------------------------------
df_fig_cov = df9

###############################################################################
#            Iterating in order to create stuff in Tableau                    #
###############################################################################
# Create a column to create the bars I want to see
df_fig_cov['amount_type'] = ""
for i in range(len(df_fig_cov)):
    if df_fig_cov['rec'][i]==True:
        df_fig_cov['amount_type'][i] = "Receipt"
    elif df_fig_cov['outlay'][i]==True:
        df_fig_cov['amount_type'][i] = "Outlay"
    else:
        df_fig_cov['amount_type'][i] = "Deficit"

# Find index value for this condition
index_tot_rec = df_fig_cov[(df_fig_cov.loc[:, 'source_func']=="Total") & (df_fig_cov.loc[:, 'rec']==True)].index.tolist()[0]
index_tot_out = df_fig_cov[(df_fig_cov.loc[:, 'source_func']=="Total") & (df_fig_cov.loc[:, 'outlay']==True)].index.tolist()[0]

# Use that index value to rename some value for another column 
df_fig_cov['amount_type'][index_tot_rec] = "Total Receipts"
df_fig_cov['amount_type'][index_tot_out] = "Total Outlays"

df_fig_cov['source_func_parent'][index_tot_rec] = "Total Receipts"
df_fig_cov['source_func_parent'][index_tot_out] = "Total Outlays"



#This is hacky to get it to appear how I want in Tableau.....................

#If receipts < outlays, then label deficit as total receipts 
    #so it'll pop up in that column in tableau
    
#Find index for deficit value
index_def = df_fig_cov[(df_fig_cov.loc[:, 'source_func']=="deficit for the month") & (df_fig_cov.loc[:, 'amount_type']=="Deficit")].index.tolist()[0]

if df_fig_cov['amt'][index_tot_rec] < df_fig_cov['amt'][index_tot_out]: # we have a deficit
    df_fig_cov['amount_type'][index_def] = "Total Receipts"
    df_fig_cov['source_func_parent'][index_def] = "Deficit"
else: #we have a surplus, put it with outlays
    df_fig_cov['amount_type'][index_def] = "Total Outlays"
    df_fig_cov['source_func_parent'][index_def] = "Surplus"
    











# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#

"""|--------------------------------------------------------------------|"""
"""|--STEP 2: MAKE df's TO DRIVE THE VISUALIZATIONS: Table 1-->Fig 1    |"""
"""|--------------------------------------------------------------------|"""


 # Figure 1 requires Table 1 ==> read that in and clean it up 


"""|--------------------------------------------------------------------|"""
"""| READ IN THE DATA - Table 1                                         |"""
"""|--------------------------------------------------------------------|"""
# Table 1 gives receipts, outlays, and surplus/deficit for previous and current FYs

#dtype was giving me errors, not sure why. perhaps read excel vs read csv thing?
path = monthly_dir + "/mts0517.xls"
whatiwant = {col: str for col in (0,3)}
df1 = pd.read_excel(path, 
                   sheetname="Table 1", 
                   header=2, 
                   skiprows=[3, 18], 
                   converters=whatiwant)


"""|--------------------------------------------------------------------|"""
"""| WRANGLE THE DATA - Table 1                                         |"""
"""|--------------------------------------------------------------------|"""

### Create a Fiscal Year Column -----------------------------------------------
df1.rename(columns ={'Period': 'month'}, inplace = True)
df1.rename(columns ={'Receipts': 'recpt'}, inplace = True)
df1.rename(columns ={'Outlays': 'outlay'}, inplace = True)
df1.rename(columns ={'Deficit/Surplus (-)': 'deficit'}, inplace = True)

prev_fy = df1['month'][0]
prev_fy = prev_fy[3:]
curr_fy = str(int(prev_fy) + 1)

df1['fy'] = ""

for i in range(1,14):
    df1['fy'][i] = prev_fy

for i in range(14, len(df1)):
    df1['fy'][i] = curr_fy


### Drop rows -----------------------------------------------------------------
df1['month'] = df1['month'].str.strip()
df1['month'] = df1['month'].astype(str)
df1 = df1[(df1['month'] != 'nan')]
df1 = df1[(df1['month'] != ". Note: Details may not add to totals due to rounding.")]
df1 = df1[(df1['month'] != 'Year-to-Date')]
df1.drop(df1.index[0], inplace=True)
df1.reset_index(drop=True, inplace=True)
### Add in cumulative sum columns ----------------------------------------------

# remove all commas
df1['recpt'] = df1['recpt'].str.replace(',', '')
df1['outlay'] = df1['outlay'].str.replace(',', '')
df1['deficit'] = df1['deficit'].str.replace(',', '')

# make an integer
df1['recpt'] = df1['recpt'].astype(float)
df1['outlay'] = df1['outlay'].astype(float)
df1['deficit'] = df1['deficit'].astype(float)

# Create cum sum columns ----------------------------------------------------

# First, split by year
g = df1[(df1['fy'] != curr_fy)] #this is just 2016
h = df1[(df1['fy'] != prev_fy)] #this is just 2017


#Next, find cumulative sum for that year 
g['recpt_ytd'] = g['recpt'].cumsum()
g['outlays_ytd'] = g['outlay'].cumsum()
g['deficit_ytd'] = g['deficit'].cumsum()

h['recpt_ytd'] = h['recpt'].cumsum()
h['outlays_ytd'] = h['outlay'].cumsum()
h['deficit_ytd'] = h['deficit'].cumsum()

#Put them back together

df1 = pd.concat([g, h], axis=0, ignore_index=True)



### Create dataframe for the figure (R/O only) -------------------------------
df_fig1 = df1[['month',
               'fy',
               'recpt',
               'outlay',
               'deficit']]


###############################################################################
#            Iterating in order to create stuff in Tableau                    #
###############################################################################


### Create a negative version of outlays so Tableau can plot  -----------------
df_fig1['neg_outlays'] = -1*df_fig1['outlay']


### Create a categorical variable for coloring purposes in Tableau ------------
df_fig1['amt_type'] = ""


### Make long by having only one "amount" column 
    # and indicate type in separate variable------------------------------------

x = df_fig1[['month',
               'fy',
               'recpt',
               'amt_type']]
x['amt_type'] = "Receipt"



y = df_fig1[['month',
               'fy',
               'outlay',
               'amt_type']]

y['amt_type'] = "Outlay"



z = df_fig1[['month',
               'fy',
               'deficit',
               'amt_type']]
z['amt_type'] = "Deficit"





df_fig1_v6 = pd.concat([x, y], axis=0, ignore_index=True)
df_fig1_v6 = pd.concat([df_fig1_v6, z], axis=0, ignore_index=True)

df_fig1_v6.reset_index(drop=True, inplace=True)


### Add date column that combines month and fiscal year for Tableau -----------

    # v6
df_fig1_v6['date'] = df_fig1_v6['month'] + ", " + df_fig1_v6['fy']   

### Creating a jacked up dataset to recreate 
    # Justin/Howie's version 10a ----------------------------------------------
y['neg_outlays'] = -1*y['outlay']

x.rename(columns ={'recpt': 'amount_RO'}, inplace = True)
y.rename(columns ={'neg_outlays': 'amount_RO'}, inplace = True)
z.rename(columns ={'deficit': 'amount_DS'}, inplace = True)


df_fig1_10a = pd.merge(x,z, on= ["month", "fy"], how='outer', indicator= "LxRz")
df_fig1_10a.columns.tolist()

df_fig1_10a = df_fig1_10a[['month', 'fy', 'amount_RO', 'amt_type_x', 'amount_DS']]
df_fig1_10a.rename(columns ={'amt_type_x': 'amt_type'}, inplace = True)
df_fig1_10a = pd.concat([df_fig1_10a, y], axis=0, ignore_index=True)

del df_fig1_10a['outlay']

### Add date column that combines month and fiscal year for Tableau -----------
 
    #v 10a
df_fig1_10a['date'] = df_fig1_10a['month'] + ", " + df_fig1_10a['fy'] 


### Make deficit numbers negative so Tableau knows how to plot them
df_fig1_v6['deficit_as_neg'] = -1*df_fig1_v6['deficit']
df_fig1_10a['deficit_as_neg'] = -1*df_fig1_10a['amount_DS']




# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#

"""|--------------------------------------------------------------------|"""
"""|--STEP 3: MAKE df's TO DRIVE THE VISUALIZATIONS: Table 1-->Fig 2    |"""
"""|--------------------------------------------------------------------|"""

### Create dataframe for the figure (YTD only) -------------------------------
df1.columns.tolist()

df_fig2 = df1[['month',
               'fy',
               'recpt_ytd',
               'outlays_ytd',
               'deficit_ytd']]


###############################################################################
#            Iterating in order to create stuff in Tableau (Fig 2)            #
###############################################################################


### Create a negative version of outlays in case I need that -----------------
df_fig2['neg_outlays_fytd'] = -1*df_fig2['outlays_ytd']


### Create a categorical variable for coloring purposes in Tableau ------------
df_fig2['amt_type'] = ""


### Make long by having only one "amount" column 
    # and indicate type in separate variable------------------------------------

x = df_fig2[['month',
               'fy',
               'recpt_ytd',
               'amt_type']]
x['amt_type'] = "Receipt"



y = df_fig2[['month',
               'fy',
               'neg_outlays_fytd',
               'amt_type']]

y['amt_type'] = "Outlay"



z = df_fig2[['month',
               'fy',
               'deficit_ytd',
               'amt_type']]
z['amt_type'] = "Deficit"





df_fig2_v6 = pd.concat([x, y], axis=0, ignore_index=True)
df_fig2_v6 = pd.concat([df_fig2_v6, z], axis=0, ignore_index=True)

df_fig2_v6.reset_index(drop=True, inplace=True)


### Add date column that combines month and fiscal year for Tableau -----------

    # v6
df_fig2_v6['date'] = df_fig2_v6['month'] + ", " + df_fig2_v6['fy']   

### Creating a jacked up dataset to recreate 
    # Justin/Howie's version 10a ----------------------------------------------
x.rename(columns ={'recpt_ytd': 'amount_RO_fytd'}, inplace = True)
y.rename(columns ={'neg_outlays_fytd': 'amount_RO_fytd'}, inplace = True)
z.rename(columns ={'deficit_ytd': 'amount_DS_fytd'}, inplace = True)



df_fig2_10a = pd.merge(x,z, on= ["month", "fy"], how='outer', indicator= "LxRz")
df_fig2_10a.columns.tolist()

df_fig2_10a = df_fig2_10a[['month',
 'fy',
 'amount_RO_fytd',
 'amt_type_x',
 'amount_DS_fytd']]
df_fig2_10a.rename(columns ={'amt_type_x': 'amt_type'}, inplace = True)
df_fig2_10a = pd.concat([df_fig2_10a, y], axis=0, ignore_index=True)


### Add date column that combines month and fiscal year for Tableau -----------
 
    #v 10a
df_fig2_10a['date'] = df_fig2_10a['month'] + ", " + df_fig2_10a['fy'] 


### Make deficit numbers negative so Tableau knows how to plot them
df_fig2_v6['deficit_fytd_as_neg'] = -1*df_fig2_v6['deficit_ytd']
df_fig2_10a['deficit_fytd_as_neg'] = -1*df_fig2_10a['amount_DS_fytd']


# Fig 2, v6 -------------------------------------------------------------------
#-- need positive outlays fytd
df_fig2_v6.columns.tolist()

df_fig2_v6['neg_outlays_fytd'] = -1*(df_fig2_v6['neg_outlays_fytd'])
df_fig2_v6.rename(columns ={'neg_outlays_fytd': 'outlays_fytd'}, inplace = True)






# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#


"""|--------------------------------------------------------------------------|"""
"""|--STEP 5: MAKE df's TO DRIVE THE VISUALIZATIONS: Table 9's --> Fig 3, 4   |"""
"""|--------------------------------------------------------------------------|"""

# Figure 4 needs outlays for Fy16 and FY17 by FUNCTION 
    # i.e. Table 9 from the past 12-24 MTS's

os.chdir(monthly_dir) #change working directory to data in GA folder
os.listdir(os.getcwd()) #list out files in there 



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


list_of_dfs = [pd.read_csv(x, index_col=0, encoding = 'latin1') for x in df9_filename_list if x.startswith("df9")]

 # For longer datasets, this can hit performance hard, so be efficient with RAM/memory
 # and do 2 at a time then delete 


df9_master = list_of_dfs[0]
starting_index = len(list_of_dfs)-1
for i in range(starting_index, 0, -1):
    df9_master = pd.concat([df9_master, list_of_dfs[i]], ignore_index = True)
    del list_of_dfs[i]




### Write to CSV --------------------------------------------------------------
df9_master.to_csv(output_dir + "/masters/master_df9" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)




"""|--------------------------------------------------------------------|"""
"""|--STEP X: MAKE df's TO DRIVE THE VISUALIZATIONS: Table 9-->Fig 3    |"""
"""|--------------------------------------------------------------------|"""

### Create dataframe for the figure (YTD only) -------------------------------
df9_master.columns.tolist()

df_fig3 = df9_master[['fy',
                      'month',
                      'amt',
                      'rec',
                      'outlay',
                      'source_func_parent']]

# Drop row if value in "receipts" column equals true ---------------------------
df_fig3 = df_fig3[df_fig3['rec']==True]

# Drop one column by name - drop outlay col, rec col 
del df_fig3['rec']
del df_fig3['outlay']

# Create a date column for Tableau to turn into one date (e.g. 10/1/16)--------
df_fig3['date'] = ""
df_fig3['month'] = df_fig3['month'].astype(str)
df_fig3['fy'] = df_fig3['fy'].astype(str)
df_fig3['date'] = df_fig3['month'] + "-" + df_fig3['fy']  

# Rename column ---------------------------------------------------------------
df_fig3.rename(columns= {"amt" : "receipt_amount"}, inplace=True)

# Reset index
df_fig3.reset_index(drop=True, inplace=True)






"""|--------------------------------------------------------------------|"""
"""|--STEP X: MAKE df's TO DRIVE THE VISUALIZATIONS: Table 9-->Fig 4    |"""
"""|--------------------------------------------------------------------|"""

### Create dataframe for the figure ------------------------------------------
df_fig4 = df9_master[['fy',
                      'month',
                      'amt',
                      'rec',
                      'outlay',
                      'source_func_parent']]



# Drop row if value in "outlays" column equals true ---------------------------
df_fig4 = df_fig4[df_fig4['outlay']==True]

# Drop one column by name - drop outlay col, rec col 
del df_fig4['rec']
del df_fig4['outlay']



# Create a date column for Tableau to turn into one date (e.g. 10/1/16)--------
df_fig4['date'] = ""
df_fig4['month'] = df_fig4['month'].astype(str)
df_fig4['fy'] = df_fig4['fy'].astype(str)
df_fig4['date'] = df_fig4['month'] + "-" + df_fig4['fy']  

# Rename column ---------------------------------------------------------------
df_fig4.rename(columns= {"amt" : "outlay_amount"}, inplace=True)

# Reset index
df_fig4.reset_index(drop=True, inplace=True)


df_fig4 = df_fig4[df_fig4['source_func_parent'] != ". (**) Less than absolute value of $500,000"]


# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#

"""|--------------------------------------------------------------------|"""
"""| Convert numbers to absolute numbers                                |"""
"""|--------------------------------------------------------------------|"""

"""Notes on (df, table, )

Scale - All tables display millions 

df_fig_cov - Table 9 - millions
df_fig1 - Table 1 - millions
df_fig2 - Table 1 - millions 
df_fig3 - Table 9 
df_fig4 - Table 9 

"""
# COVER FIGURE ---------------------------------------------------------------
df_fig_cov.columns.tolist()

# Rename the old columns as ($M)
df_fig_cov.rename(columns ={'amt': 'amt_M'}, inplace = True)
df_fig_cov.rename(columns ={'fytd': 'fytd_M'}, inplace = True)
df_fig_cov.rename(columns ={'comp_per_pfy': 'comp_per_pfy_M'}, inplace = True)

# Create columns with absolute numbers
df_fig_cov['amt'] = df_fig_cov['amt_M']*1000000
df_fig_cov['fytd'] = df_fig_cov['fytd_M']*1000000
df_fig_cov['comp_per_pfy'] = df_fig_cov['comp_per_pfy_M']*1000000

# FIGURE 1, v6-------------------------------------------------------------------
df_fig1_v6.columns.tolist()

# Rename the old columns as ($M)
df_fig1_v6.rename(columns ={'recpt': 'recpt_M'}, inplace = True)
df_fig1_v6.rename(columns ={'outlay': 'outlay_M'}, inplace = True)
df_fig1_v6.rename(columns ={'deficit': 'deficit_M'}, inplace = True)
df_fig1_v6.rename(columns ={'deficit_as_neg': 'deficit_as_neg_M'}, inplace = True)

# Create columns with absolute numbers
df_fig1_v6['receipts'] = df_fig1_v6['recpt_M']*1000000
df_fig1_v6['outlays'] = df_fig1_v6['outlay_M']*1000000
df_fig1_v6['deficit'] = df_fig1_v6['deficit_M']*1000000
df_fig1_v6['deficit_as_neg'] = df_fig1_v6['deficit_as_neg_M']*1000000


# FIGURE 1, v10a-------------------------------------------------------------------
df_fig1_10a.columns.tolist()

# Rename the old columns as ($M)
df_fig1_10a.rename(columns ={'amount_DS': 'amount_DS_M'}, inplace = True)
df_fig1_10a.rename(columns ={'amount_RO': 'amount_RO_M'}, inplace = True)
df_fig1_10a.rename(columns ={'deficit_as_neg': 'deficit_as_neg_M'}, inplace = True)

# Create columns with absolute numbers
df_fig1_10a['amount_DS'] = df_fig1_10a['amount_DS_M']*1000000
df_fig1_10a['amount_RO'] = df_fig1_10a['amount_RO_M']*1000000
df_fig1_10a['deficit_as_neg'] = df_fig1_10a['deficit_as_neg_M']*1000000
           

df_fig1_10a.columns.tolist()

df_fig1_10a = df_fig1_10a[['date',
  'amt_type',
 'amount_DS',
 'amount_RO',
 'deficit_as_neg']]


# FIGURE 2, v6-------------------------------------------------------------------
df_fig2_v6.columns.tolist()

# Rename the old columns as ($M)
df_fig2_v6.rename(columns ={'deficit_ytd': 'deficit_ytd_M'}, inplace = True)
df_fig2_v6.rename(columns ={'outlays_fytd': 'outlays_fytd_M'}, inplace = True)
df_fig2_v6.rename(columns ={'recpt_ytd': 'recpt_ytd_M'}, inplace = True)
df_fig2_v6.rename(columns ={'deficit_fytd_as_neg': 'deficit_fytd_as_neg_M'}, inplace = True)

# Create columns with absolute numbers
df_fig2_v6['deficit_ytd'] = df_fig2_v6['deficit_ytd_M']*1000000
df_fig2_v6['outlays_fytd'] = df_fig2_v6['outlays_fytd_M']*1000000
df_fig2_v6['recpt_ytd'] = df_fig2_v6['recpt_ytd_M']*1000000
df_fig2_v6['deficit_fytd_as_neg'] = df_fig2_v6['deficit_fytd_as_neg_M']*1000000
       
# FIGURE 2, v10a-------------------------------------------------------------------
df_fig2_10a.columns.tolist()

# Rename the old columns as ($M)
df_fig2_10a.rename(columns ={'amount_DS_fytd': 'deficit_ytd_M'}, inplace = True)
df_fig2_10a.rename(columns ={'amount_RO_fytd': 'outlays_fytd_M'}, inplace = True)
df_fig2_10a.rename(columns ={'deficit_fytd_as_neg': 'recpt_ytd_M'}, inplace = True)


# Create columns with absolute numbers
df_fig2_10a['amount_DS_fytd'] = df_fig2_10a['deficit_ytd_M']*1000000
df_fig2_10a['amount_RO_fytd'] = df_fig2_10a['outlays_fytd_M']*1000000
df_fig2_10a['deficit_fytd_as_neg'] = df_fig2_10a['recpt_ytd_M']*1000000
           
           


# FIGURE 3 -------------------------------------------------------------------
df_fig3.columns.tolist()

# Rename the old columns as ($M)
df_fig3.rename(columns ={'receipt_amount': 'receipt_amount_M'}, inplace = True)

# Create columns with absolute numbers
df_fig3['receipt_amount'] = df_fig3['receipt_amount_M']*1000000

# FIGURE 3 -------------------------------------------------------------------
df_fig4.columns.tolist()

# Rename the old columns as ($M)
df_fig4.rename(columns ={'outlay_amount': 'outlay_amount_M'}, inplace = True)

# Create columns with absolute numbers
df_fig4['outlay_amount'] = df_fig4['outlay_amount_M']*1000000
       
          
          
"""|--------------------------------------------------------------------|"""
"""| COMBINE CATEGORIES (e.g. EstateTax and Estate Tax) and GROUPBY/SUM |"""
"""|--------------------------------------------------------------------|"""

### Figure 3 -----------------------------------------------------------------
df_fig3['source_func_parent'].unique()


    # Estate and Gift Taxes & Customs Duties

df_fig3['source_func_parent_2'] = np.where(df_fig3['source_func_parent']=="Estate andGift Taxes", 'Estate and Gift Taxes', df_fig3['source_func_parent'])
df_fig3['source_func_parent_2'] = np.where(df_fig3['source_func_parent']=="CustomsDuties", 'Customs Duties', df_fig3['source_func_parent_2'])

del df_fig3['source_func_parent']
df_fig3.rename(columns ={'source_func_parent_2': 'source_func_parent'}, inplace = True)


### Figure 3 -----------------------------------------------------------------
#functions = df_fig4['source_func_parent'].unique().tolist()

    #Income Security, Social Security 
df_fig4['source_func_parent_2'] = np.where(df_fig4['source_func_parent']=="IncomeSecurity", 'Income Security', df_fig4['source_func_parent'])
df_fig4['source_func_parent_2'] = np.where(df_fig4['source_func_parent']=="SocialSecurity", 'Social Security', df_fig4['source_func_parent_2'])

del df_fig4['source_func_parent']
df_fig4.rename(columns ={'source_func_parent_2': 'source_func_parent'}, inplace = True)




"""|--------------------------------------------------------------------|"""
"""| Add monthly totals for Tableau to label                            |"""
"""|--------------------------------------------------------------------|"""

### Figure 3 ----------------------------------------------------------------
df_fig3.reset_index(drop=True, inplace=True)
df_fig3['total_R_month']=""

list_dates_df_fig3 = df_fig3['date'].unique().tolist()

for i in range(len(df_fig3)):
    
    for v in list_dates_df_fig3:
        index_tot_rec = df_fig3[(df_fig3['source_func_parent']=="Total") & (df_fig3['date']==str(v))].index.tolist()[0] 
        monthly_total_R = df_fig3['receipt_amount'][index_tot_rec]
    
        if df_fig3['date'][i]==str(v):    
            df_fig3['total_R_month'][i] = monthly_total_R


df_fig3['total_R_month'] = df_fig3['total_R_month'].astype(float)



### Figure 4 ----------------------------------------------------------------
df_fig4.reset_index(drop=True, inplace=True)
df_fig4.columns.tolist()
df_fig4['total_OL_month']=""

list_dates_df_fig4 = df_fig4['date'].unique().tolist()

for i in range(len(df_fig4)):
    
    for v in list_dates_df_fig4:
        index_tot_out = df_fig4[(df_fig4['source_func_parent']=="Total") & (df_fig4['date']==str(v))].index.tolist()[0] 
        monthly_total_OL = df_fig4['outlay_amount'][index_tot_out]
    
        if df_fig4['date'][i]==str(v):    
            df_fig4['total_OL_month'][i] = monthly_total_OL


df_fig4['total_OL_month'] = df_fig4['total_OL_month'].astype(float)





# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#

"""|--------------------------------------------------------------------|"""
"""| WRITE THESE FIG DATASETS TO CSV                                    |"""
"""|--------------------------------------------------------------------|"""
df_fig_cov.to_csv(output_dir + "/figure_datasets/fig_cover_" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)

df_fig1_10a.to_csv(output_dir + "/figure_datasets/fig1_v10a_" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)
df_fig1_v6.to_csv(output_dir + "/figure_datasets/fig1_v6_" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)

df_fig2_10a.to_csv(output_dir + "/figure_datasets/fig2_v10a_" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)
df_fig2_v6.to_csv(output_dir + "/figure_datasets/fig2_v6_" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)

df_fig3.to_csv(output_dir + "/figure_datasets/fig3_" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)

df_fig4.to_csv(output_dir + "/figure_datasets/fig4_" + str(current_mo) + str(current_fy) + ".csv", index=False, header=True)


























