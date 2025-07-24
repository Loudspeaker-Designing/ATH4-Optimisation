import os
import configparser
import pandas as pd
import bisect
import re

# Load configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Paths from config.ini
RESULTS_FOLDER = config['Paths']['results_folder']
TARGETDI = config['Paths']['di_target']

def read_target(di_target):
    return pd.read_table(di_target, sep=None, header=None, engine='python', encoding='utf-8-sig')

def score(di_folder, target_di_tbl):
    di_files = [f for f in os.listdir(di_folder) if f"-DI.txt" in f]

    names = ['frequency', 'measured']
    correls = ['', 1]
    sub_correls = ['', 1]
    params = [['c', 'x', 'a'], ['', '', '']]

    target_row_data = target_di_tbl.transpose()
    # could do this better
    freq_row = 0
    sub_lo = bisect.bisect_right(target_row_data.iloc[freq_row].tolist(), 8500)
    sub_hi = bisect.bisect_right(target_row_data.iloc[freq_row].tolist(), 17000)

    vals_list = target_row_data.values.tolist()
    for file in di_files:
        condition = file.replace("-DI.txt", "")
        c, x, a = re.findall(r'\d+\.\d+', condition)
        names.append(condition)
        params.append([c,x,a])
        src = os.path.join(di_folder, file)
        print(f'Reading: {file}')
        src_di_tbl = pd.read_table(src, sep=None, header=None, engine='python').transpose()
        correls.append(target_row_data.iloc[1].corr(src_di_tbl.iloc[1]))
        sub_correls.append(target_row_data.iloc[1, sub_lo:sub_hi].corr(src_di_tbl.iloc[1, sub_lo:sub_hi]))
        vals_list.append(src_di_tbl.iloc[1].tolist())

    vals_tbl = pd.DataFrame(vals_list)
    params_T = [list(row) for row in zip(*params)]
    info = [names]
    info.extend(params_T) # Note need to add contents, not list
    info.append(correls)
    info.append(sub_correls)
    info_T = [list(row) for row in zip(*info)]
    # print(info_T)
    out = pd.concat([pd.DataFrame(info_T), vals_tbl], axis=1)
    out.to_csv(os.path.join(di_folder, 'DI-scores.csv'), index=False)
    print(f'Saved to: {os.path.join(di_folder, "DI-scores.csv")}')

# Main execution
if __name__ == "__main__":
    di_target = read_target(TARGETDI)
    score(RESULTS_FOLDER, di_target)
