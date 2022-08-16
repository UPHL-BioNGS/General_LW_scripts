#!/usr/bin/env python
# coding: utf-8


import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import re
import os
import glob
import copy
import matplotlib.dates as mdates
import numpy as np
import sys

run_name = sys.argv[1]
filepath = os.getcwd()
print(filepath)

#Read in the lineage aggregate result file;freyja summary output
source_files = glob.glob('*lineages_aggregate.tsv')

for file in source_files:
	print(file)
new_agg_df_all = pd.read_csv(file, sep="\t", index_col=0)
#print(new_agg_df_all)

#Remove any missing values rows otherwsie it breaks the code
new_agg_df_all = new_agg_df_all.dropna(axis=0, how='any')

def prepLineageDict(agg_d0, thresh=0.001, config=None, lineage_info=None):
    agg_d0.loc[:, 'lineages'] = agg_d0['lineages'].apply(lambda x:
                                                         re.sub(' +', ' ', x)
                                                           .split(' ')).copy()
    agg_d0.loc[:, 'abundances'] = agg_d0['abundances'].apply(lambda x:
                                                            re.sub(' +', ' ', x)
                                                              .split(' ')).copy()
    # print([float(abund) for abund in agg_d0.iloc[0].loc['abundances']])
    #Create 'linDict' column with mapped lineages and abundances values
    agg_d0.loc[:, 'linDict'] = [{lin: float(abund) for lin, abund in
                                zip(agg_d0.loc[samp, 'lineages'],
                                    agg_d0.loc[samp, 'abundances'])}
                                for samp in agg_d0.index]

   
    return agg_d0

new_agg_df_all_dict = prepLineageDict(new_agg_df_all)

#print(new_agg_df_all_dict.index)

#For direct freyja results
#Shorten the sample names to remove '_out_variants.tsv' Please note that the separatore has changed after the recent viralrecon update
new_agg_df_all_dict.index = [x.split('_out')[-2] for x in new_agg_df_all_dict.index]
#print(new_agg_df_all_dict.index)

#Get the lineage dictionary and convert dictionary to df
my_lin_dict = new_agg_df_all_dict.loc[:, 'linDict']
my_dict_df = pd.DataFrame(my_lin_dict, index=None)
my_dict_df .reset_index(inplace=True)
#print(my_dict_df )

#Creating matrix from lineage dictionary
dict_df_matrix = pd.DataFrame(my_dict_df['linDict'].values.tolist(), index=my_dict_df['index'])
#print(dict_df_matrix)

round(dict_df_matrix, 3)

dict_df_matrix.reset_index(inplace=True)

#edit index names if needed, replace "-" with "_"
dict_df_matrix.loc[:, 'index'] = dict_df_matrix['index'].apply(lambda x: x.replace("-", "_"))

#melting matrix to long df
dict_df_matrix_melt = pd.melt(dict_df_matrix,id_vars=['index'],var_name='lineages', value_name='abundance')

dict_df_matrix_melt_noNA = dict_df_matrix_melt.dropna(axis=0, how='any')

#Save the long df output
dict_df_matrix_melt_noNA.to_csv(f'{run_name}_freyja_lin_dict_long_df.csv', sep=',')

#Below are the optional steps to add an additional column of 'Lineages' for 'sub-lineages' in the data output
uniq_lineage_list = dict_df_matrix_melt_noNA.lineages.unique()

np.savetxt('freyja_uniq_lineage_list.csv', uniq_lineage_list, fmt='%s', delimiter = ",")

#Get the unique lineages detected in the current run
uniq_lineage = pd.read_csv("freyja_uniq_lineage_list.csv",
                 names=["lineages"])

#Adding parent lineage grouping for each the lineages (This may need to be updated when a new sub-lineage is designated) 
uniq_lineage['Parent_lineage'] = np.where(uniq_lineage.lineages.str.startswith('BA.5'), 'Omicron (BA.5)',
                                np.where(uniq_lineage.lineages.str.startswith('BA.4'), 'Omicron (BA.4)', 
                                np.where(uniq_lineage.lineages.str.startswith('BA.3'), 'Omicron (BA.3)',
                                np.where(uniq_lineage.lineages.str.startswith('BA.2'), 'Omicron (BA.2)',
                                np.where(uniq_lineage.lineages.str.startswith('BA.1'), 'Omicron (BA.1)',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.1.529'), 'Omicron',
                                np.where(uniq_lineage.lineages.str.startswith('BC'), 'Omicron (BA.1)',
                                np.where(uniq_lineage.lineages.str.startswith('BD'), 'Omicron (BA.1)',
                                np.where(uniq_lineage.lineages.str.startswith('BE'), 'Omicron (BA.5)',
                                np.where(uniq_lineage.lineages.str.startswith('BF'), 'Omicron (BA.5)',
                                np.where(uniq_lineage.lineages.str.startswith('BG'), 'Omicron (BA.2)',
                                np.where(uniq_lineage.lineages.str.startswith('Q'), 'Alpha',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.1.7'), 'Alpha',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.351'), 'Beta',         
                                np.where(uniq_lineage.lineages.str.startswith('P.1'), 'Gamma',
                                np.where(uniq_lineage.lineages.str.startswith('P.2'), 'Zeta',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.617.1'), 'Kappa',
                                np.where(uniq_lineage.lineages.str.startswith('AY'), 'Delta (AY)',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.617.2'), 'Delta',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.427'), 'Epsilon',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.429'), 'Epsilon',         
                                np.where(uniq_lineage.lineages.str.startswith('B.1.525'), 'Eta',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.526'), 'Iota',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.621'), 'Mu',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.1'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.2'), 'B.1.2',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.3'), 'B.1.3',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.4'), 'B.1.4',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.5'), 'B.1.5',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.6'), 'B.1.6',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.7'), 'B.1.7',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.8'), 'B.1.8',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.9'), 'B.1.9',
                                np.where(uniq_lineage.lineages.str.startswith('AC'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AD'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AE'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AF'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AH'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AK'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AS'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AT'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AZ'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('P.'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('A.1'), 'A.1',
                                np.where(uniq_lineage.lineages.str.startswith('A.2'), 'A.2',
                                np.where(uniq_lineage.lineages.str.startswith('A.3'), 'A.3',
                                np.where(uniq_lineage.lineages.str.startswith('A.4'), 'A.4',
                                np.where(uniq_lineage.lineages.str.startswith('A.5'), 'A.5',
                                np.where(uniq_lineage.lineages.str.startswith('A.6'), 'A.6',
                                np.where(uniq_lineage.lineages.str.startswith('A.7'), 'A.7',
                                np.where(uniq_lineage.lineages.str.startswith('A'), 'A',
                                np.where(uniq_lineage.lineages.str.startswith('C.'), 'B.1.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('D'), 'B.1.1.25',
                                np.where(uniq_lineage.lineages.str.startswith('L.'), 'B.1.1.10',
                                np.where(uniq_lineage.lineages.str.startswith('M.'), 'B.1.1.216',
                                np.where(uniq_lineage.lineages.str.startswith('N.'), 'B.1.1.33',
                                np.where(uniq_lineage.lineages.str.startswith('P'), 'B.1.1.28',
                                np.where(uniq_lineage.lineages.str.startswith('R'), 'B.1.1.316',         
                                np.where(uniq_lineage.lineages.str.startswith('B.1'), 'B.1',
                                np.where(uniq_lineage.lineages.str.startswith('X'), 'Recombinant',
                                np.where(uniq_lineage.lineages.str.startswith('miscRecombOrContam'), 'miscRecombOrContam', 'NA')))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))


uniq_lineage.to_csv("freyja_uniq_lineage_w_lin_grps.csv", sep=',', index=0)

#Merge the unique lineages file (With the lineage groups) with the dictionaery long df file
dict_df_matrix_melt_noNA_lingrps = pd.merge(dict_df_matrix_melt_noNA,uniq_lineage, on='lineages')

dict_df_matrix_melt_noNA_lingrps = dict_df_matrix_melt_noNA_lingrps.rename(columns = {'index': 'sample_id'})

#Add an index column to help parse the file in Microreact (Microreact requires a unique ID column)
dict_df_matrix_melt_noNA_lingrps.index.name = 'idx_name'

#change the run name for the file output before saving the file
dict_df_matrix_melt_noNA_lingrps.to_csv(f'{run_name}_freyja_lin_dict_long_df_lingrps_final.csv', sep=',', index=1)