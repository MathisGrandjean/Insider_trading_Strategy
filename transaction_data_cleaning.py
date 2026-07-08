# -*- coding: utf-8 -*-
"""
Created on Sun May 24 10:01:45 2026

@author: Mathis
"""

import pandas as pd
import os 
from config import DATA_DIR

def clean_insider_data(submission,reporting,transactions):
    submission = submission[['ACCESSION_NUMBER', 'FILING_DATE', 'PERIOD_OF_REPORT', 'DOCUMENT_TYPE', 'ISSUERCIK', 'ISSUERNAME', 'ISSUERTRADINGSYMBOL']]
    submission=submission.rename(columns={
        'ACCESSION_NUMBER'    : 'accession_number',
        'FILING_DATE'         : 'filing_date',
        'PERIOD_OF_REPORT'    : 'period_of_report',
        'DOCUMENT_TYPE'       : 'document_type',
        'ISSUERCIK'           : 'issuer_cik',
        'ISSUERNAME'          : 'issuer_name',
        'ISSUERTRADINGSYMBOL' : 'ticker'
    })
                                  
                            
    reporting = reporting[['ACCESSION_NUMBER', 'RPTOWNERCIK', 'RPTOWNERNAME', 'RPTOWNER_RELATIONSHIP', 'RPTOWNER_TITLE']]
    reporting=reporting.rename(columns={
        'ACCESSION_NUMBER'    : 'accession_number',
        'RPTOWNERCIK'         : 'owner_cik',
        'RPTOWNERNAME'        : 'owner_name',
        'RPTOWNER_RELATIONSHIP': 'relationship',
        'RPTOWNER_TITLE'      : 'title'
    })
    
    
    transactions = transactions[['ACCESSION_NUMBER', 'TRANS_DATE', 'TRANS_CODE','SECURITY_TITLE','DEEMED_EXECUTION_DATE',
                                  'TRANS_SHARES', 'TRANS_PRICEPERSHARE', 'TRANS_TIMELINESS',
                                  'TRANS_ACQUIRED_DISP_CD', 'SHRS_OWND_FOLWNG_TRANS']]
    
    transactions=transactions.rename(columns={
        'ACCESSION_NUMBER'      : 'accession_number',
        'SECURITY_TITLE': 'security_type',
        'DEEMED_EXECUTION_DATE' : 'execution_date',
        'TRANS_TIMELINESS' : 'time_transaction',
        'TRANS_DATE'            : 'trans_date',
        'TRANS_CODE'            : 'trans_code',
        'TRANS_SHARES'          : 'shares',
        'TRANS_PRICEPERSHARE'   : 'price',
        'TRANS_ACQUIRED_DISP_CD': 'acquired_disp',
        'SHRS_OWND_FOLWNG_TRANS': 'shares_owned_after'
    })
                                      
    keep_code = ['P', 'S']
    
    transactions = transactions[transactions['trans_code'].isin(keep_code)]
    
    merge = submission.merge(reporting, on='accession_number', how= 'left')
    
    merge_transaction = transactions.merge(merge, on='accession_number', how= 'left') 
    #4A amendement sur transactions déjà déposé 
    merge_transaction = merge_transaction[merge_transaction['document_type'] == '4']
    date_cols = ['trans_date', 'filing_date', 'period_of_report']
    
    for col in date_cols:
        merge_transaction[col] = pd.to_datetime(merge_transaction[col], format='mixed')
    merge_transaction['net_shares'] = merge_transaction.apply(
        lambda x: x['shares'] if x['acquired_disp'] == 'A' else -x['shares'], axis=1
    )
    merge_transaction = merge_transaction.drop_duplicates(keep='first')
    return merge_transaction.reset_index(drop=True)

    return merge_transaction
# %%


def load_all_quarters(base_path ,collect_all ):

    folders = sorted([
        f for f in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, f))
    ])

    if not folders:
        raise ValueError(f"Aucun sous-dossier trouvé dans {base_path}")

    if not collect_all:
        folders = [folders[-1]]

    all_dfs = []

    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        try:
            submission   = pd.read_csv(f"{folder_path}/SUBMISSION.tsv",     sep='\t', encoding='utf-8', low_memory=False)
            reporting    = pd.read_csv(f"{folder_path}/REPORTINGOWNER.tsv",  sep='\t', encoding='utf-8', low_memory=False)
            transactions = pd.read_csv(f"{folder_path}/NONDERIV_TRANS.tsv",  sep='\t', encoding='utf-8', low_memory=False)

            df = clean_insider_data(submission, reporting, transactions)
            all_dfs.append(df)
        except Exception as e:
            print(f" {folder} — {e}")

    return pd.concat(all_dfs, ignore_index=True)


path = DATA_DIR / "data_insider"
 
df_all = load_all_quarters(path, collect_all=True)
df_all.to_parquet(DATA_DIR / 'insider_trading_database.parquet')
