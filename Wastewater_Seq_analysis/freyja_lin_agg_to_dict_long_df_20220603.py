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
print(new_agg_df_all)


def prepLineageDict(agg_d0, thresh=0.001):
    agg_d0.loc[:, 'lineages'] = agg_d0['lineages']          .apply(lambda x:
                 x.replace("'", "")
                  .replace("]", "")
                  .replace("[", "")
                  .replace(")", "")
                  .replace("(", "")
                  .replace("\n", "")).copy()
    agg_d0 = agg_d0[agg_d0['lineages'].apply(lambda x: len(x) > 0)].copy()
    agg_d0.loc[:, 'lineages'] = agg_d0['lineages'].apply(lambda x:
                                                         re.sub(' +', ' ', x)
                                                           .split(' ')).copy()
    agg_d0.loc[:, 'abundances'] = agg_d0['abundances']          .apply(lambda x:
                 x.replace("'", "")
                  .replace("]", "")
                  .replace("[", "")
                  .replace(")", "")
                  .replace("(", "")
                  .replace("\n", "")).copy()
    agg_d0.loc[:, 'abundances'] = agg_d0['abundances']          .apply(lambda x:
                 re.sub(' +', ' ', x)
                   .split(' ')).copy()
    # print([float(abund) for abund in agg_d0.iloc[0].loc['abundances']])
    agg_d0.loc[:, 'linDict'] = [{lin: float(abund) for lin, abund in
                                zip(agg_d0.loc[samp, 'lineages'],
                                    agg_d0.loc[samp, 'abundances'])}
                                for samp in agg_d0.index]

   
    return agg_d0


new_agg_df_all_dict = prepLineageDict(new_agg_df_all)


#print(new_agg_df_all_dict.index)

#For direct freyja results
#Shorten the sample names to remove '_out_variants.tsv'
new_agg_df_all_dict.index = [x.split('_out')[-2] for x in new_agg_df_all_dict.index]
#print(new_agg_df_all_dict.index)

#Get the lineage dictionary and convert dictionary to df
my_lin_dict = new_agg_df_all_dict.loc[:, 'linDict']
new_df_dict = pd.DataFrame(my_lin_dict, index=None)


new_df_dict.reset_index(inplace=True)

#print(new_df_dict)

#Creating matrix from lineage dictionary
new_df_dict_matrix = pd.DataFrame(new_df_dict['linDict'].values.tolist(), index=new_df_dict['index'])

#print(new_df_dict_matrix)

round(new_df_dict_matrix, 3)

new_df_dict_matrix.reset_index(inplace=True)


#edit index names if needed, replace "-" with "_"
new_df_dict_matrix.loc[:, 'index'] = new_df_dict_matrix['index'].apply(lambda x: x.replace("-", "_"))

#melting matrix to long df
new_df_dict_matrix_melt = pd.melt(new_df_dict_matrix,id_vars=['index'],var_name='lineages', value_name='abundance')

new_df_dict_matrix_melt_noNA = new_df_dict_matrix_melt.dropna(axis=0, how='any')

#Save the long df output
new_df_dict_matrix_melt_noNA.to_csv(f'{run_name}_freyja_lin_agg_merged_dict_long_df.csv', sep=',')

#Below are the optional steps to add an additional column of 'Lineages' for 'sub-lineages' in the data output
uniq_lineage_list = new_df_dict_matrix_melt_noNA.lineages.unique()

np.savetxt('freyja_uniq_lineage_list.csv', uniq_lineage_list, fmt='%s', delimiter = ",")


uniq_lineage = pd.read_csv("freyja_uniq_lineage_list.csv",
                 names=["lineages"])

#Adding parent lineage column for individual runs
uniq_lineage['Parent_lineage'] = np.where(uniq_lineage.lineages.str.startswith('BA.3'), 'Omicron BA.3',
                                np.where(uniq_lineage.lineages.str.startswith('BA.2'), 'Omicron BA.2',
                                np.where(uniq_lineage.lineages.str.startswith('BA.1'), 'Omicron BA.1',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.1.529'), 'Omicron',
                                np.where(uniq_lineage.lineages.str.startswith('BA.4'), 'Omicron BA.4',
                                np.where(uniq_lineage.lineages.str.startswith('BA.5'), 'Omicron BA.5',
                                np.where(uniq_lineage.lineages.str.startswith('AP'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AV'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AK'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AM'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AZ'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AT'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('P.'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('AY'), 'Delta',
                                np.where(uniq_lineage.lineages.str.startswith('A'), 'A',
                                np.where(uniq_lineage.lineages.str.startswith('B.1.'), 'B.1',
                                np.where(uniq_lineage.lineages.str.startswith('C'), 'B.1.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('X'), 'Recombinant',
                                np.where(uniq_lineage.lineages.str.startswith('Q'), 'B.1.1.7',
                                np.where(uniq_lineage.lineages.str.startswith('Z'), 'B.1.1',
                                np.where(uniq_lineage.lineages.str.startswith('miscRecombOrContam'), 'miscRecombOrContam', 'other')))))))))))))))))))))


uniq_lineage.to_csv("freyja_uniq_lineage_w_lin_grps.csv", sep=',', index=0)


new_df_dict_matrix_melt_noNA_lingrps = pd.merge(new_df_dict_matrix_melt_noNA,uniq_lineage, on='lineages')


new_df_dict_matrix_melt_noNA_lingrps = new_df_dict_matrix_melt_noNA_lingrps.rename(columns = {'index': 'sample_id'})


new_df_dict_matrix_melt_noNA_lingrps.index.name = 'idx_name'


#change the run name for the file output before saving the file
new_df_dict_matrix_melt_noNA_lingrps.to_csv(f'{run_name}_freyja_lin_dict_long_df_lingrps_final.csv', sep=',', index=1)
