"""
GOALS FOR THIS SCRIPT:
    --Explore TAS and ACCT AWARDS endpoint data without opening it up in Excel
    
    
"""

###Import stuff----------------------------------------------------------------
from __future__ import division  # imports the division capacity from the future version of Python
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
import os
import xlrd
import time
import csv
from datetime import datetime, timedelta



start = time.time()

######################## TO START #############################################
#                                                                             #
###############################################################################


### Set up directories ---------------------------------------------------------
# Where to find the API data
main_dir = "C:/Users/583902/Desktop/BAH1/_Treasury_DATA_Act/API stuff"
data_dir = main_dir + "/data"

# Output related to MTS research 
output_dir = "C:/Users/583902/Desktop/BAH1/_Treasury_DATA_Act/MTS/data/output"


### 1. READ IN THE API DATA --------------------------------------------------------

tas_bal = pd.read_csv(data_dir + "/20170613/tas_balances.csv")
tas_cat = pd.read_csv(data_dir + "/20170613/tas_categories.csv")
acct_awards = pd.read_csv(data_dir + "/20170613/accounts_awards_data.csv")


col_bal = tas_bal.columns.tolist()
col_cat = tas_cat.columns.tolist()
col_acct = acct_awards.columns.tolist()




"""

MAKE SURE YOU'RE COMPARING APPLES TO APPLES WITH BALANCES, CATOGORIES, AND PULL DATES



"""






### 2. CREATE SLIMMER DATASETS TO EXPLORE ----------------------------------------

df_slim_cat = tas_cat[[

 'reporting_period_start',
 'reporting_period_end',
 'submission.cgac_code',
 'treasury_account.fr_entity_description',
  'treasury_account.funding_toptier_agency.abbreviation',
 'treasury_account.budget_function_title',
  'treasury_account.tas_rendering_label',
 'financial_accounts_by_program_activity_object_class_id',
  'gross_outlay_amount_by_program_object_class_fyb',
 'gross_outlay_amount_by_program_object_class_cpe',
 'obligations_incurred_by_program_object_class_cpe',
 'object_class.id',
 'object_class.major_object_class',
 'object_class.major_object_class_name',
 'object_class.object_class',
 'object_class.object_class_name',
 'treasury_account.treasury_account_identifier',
 'treasury_account.awarding_toptier_agency.cgac_code',
 'treasury_account.awarding_toptier_agency.abbreviation',
 'treasury_account.funding_toptier_agency.cgac_code',
 'treasury_account.awarding_toptier_agency']]








### FIND THE TOTAL OUTLAYS PER BUDGET FUNCTION IN THE DATA ACT DATA 
    # What are outlays by budget function IN FY 17 Q2 in DATA Act data?
    # Group by budget function, then sum the outlays CPE 

grouped = df_slim_cat.groupby('treasury_account.budget_function_title')
grouped_agg = grouped['gross_outlay_amount_by_program_object_class_cpe'].sum().reset_index()


############# WRITE THIS TO CSV ###############################################

date = datetime.today().strftime("%m%d%y")
path = output_dir + "/tas_cat_outlays_by_budget_function_" + str(date) + ".csv"
grouped_agg.to_csv(path, index=False, header=True)




