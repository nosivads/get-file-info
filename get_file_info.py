# requirement: openpyxl

# notes:
# date format: yyyy-mm-dd
# date format is not validated
# if 'd' argument is given then 's' and 'e' are ignored
# 'r' and 'w' arguments are not validated

# to mount Windows mapped Box drive:
# sudo mkdir /mnt/box
# sudo mount -t drvfs 'C:Users\<USER>\Box' /mnt/box

# examples:
# python get_file_info.py -r '/mnt/box/AMT Recordings' -d 7
# python get_file_info.py -r '/mnt/box/AMT Recordings' -s 2024-06-06
# python get_file_info.py -r '/mnt/box/AMT Recordings' -e 2024-06-06
# python get_file_info.py -r '/mnt/box/AMT Recordings' -s 2024-01-01 -e 2024-01-31



import pandas as pd
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Initialize parser
parser = argparse.ArgumentParser()
parser.add_argument('-r', '--read_path', default='.')
parser.add_argument('-w', '--write_path', default='./fileinfo.xlsx')
parser.add_argument('-f', '--format', default='excel')
parser.add_argument('-d', '--days', default=0, type=int)
parser.add_argument('-s', '--start_date', default='')
parser.add_argument('-e', '--end_date', default='')

# Read arguments from command line
args = parser.parse_args()

directory = Path(args.read_path)
write_path = Path(args.write_path)
output_format = args.format
recent = args.days
if recent:
    start, end = None, None
else:
    try:
        start = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    except:
        start = None
    try:
        end = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    except:
        end = None

n = 0
filelist = list()
extensions = dict()
roots = dict()

for path in directory.rglob('*'):

    if path.is_file():

        filename = path.stem
        extension = path.suffix.lower()
        size = path.stat().st_size
        mod_date = datetime.fromtimestamp(path.stat().st_mtime).date()
        folderlist = path.relative_to(directory).parts
        if len(folderlist) > 1:
            root = folderlist[0]
        else:
            root = '' 

        if ((not recent and not start and not end) or
            (not recent and start and not end and mod_date >= start)
            or
            (not recent and not start and end and mod_date <= end)
            or
            (not recent and start and end and mod_date >= start and mod_date <= end)
            or
            (recent and (datetime.now().date() - mod_date) <= timedelta(days=recent))):

            # file information
            row = {'filename' : filename, 
                    'extension' : extension,
                    'size' : size,
                    'modified' : mod_date}
            for i, folder in enumerate(path.relative_to(directory).parts[:-1]): 
                row['folder '+str(i)] = folder
            filelist.append(row)

            # extension information
            if extension not in extensions:
                extensions[extension] = [1, size]
            else:
                extensions[extension][0] += 1
                extensions[extension][1] += size
            
            # root folder information
            if root not in roots:
                roots[root] = dict()
                roots[root][extension] = 1
            else:
                if extension not in roots[root]:
                    roots[root][extension] = 1
                else:
                    roots[root][extension] += 1

df_files = pd.DataFrame(filelist).fillna('')

df_folders = df_files.iloc[:, 4:].drop_duplicates()
cols = df_folders.columns.to_list()
df_folders = df_folders.sort_values(by=cols, key=lambda col: col.str.lower())

cols = df_files.columns.tolist()
folder_depth = len(cols[4:])
cols = cols[4:] + cols[:4]
df_files = df_files[cols].sort_values(by=cols[:folder_depth+1], key=lambda col: col.str.lower())

extensionlist = list()
for key, value in extensions.items():
    extensionlist.append({'extension' : key, 'number' : value[0], 'total size' : value[1]})
df_extensions = pd.DataFrame(extensionlist).sort_values(by=['extension'])

rootlist = list()
for key, value in roots.items():
    row = dict()
    row['root'] = key
    for ext, count in value.items():
        row[ext] = count
    rootlist.append(row)
df_roots = pd.DataFrame(rootlist).sort_values(by=['root'])
cols = df_roots.columns.tolist()
cols = cols[:1] + sorted(cols[1:])
df_roots = df_roots[cols]

size_total = df_files['size'].sum()
files_total = df_files.shape[0]
folders_total = df_folders.shape[0]
types_total = df_extensions.shape[0]
df_summary = pd.DataFrame(
    [
        ['Report date:', datetime.now().date()],
        ['Total size (bytes):', str(size_total)],
        ['Total size (MB):', str(size_total/1024/1024)],
        ['Total size (TB):', str(size_total/1024/1024/1024/1024)],
        ['Number of files:', str(files_total)],
        ['Number of folders:', str(folders_total)],
        ['Number of file types:', str(types_total)]
    ]
)

if output_format=='excel':
    with pd.ExcelWriter(write_path.name) as writer:
        df_summary.to_excel(writer, sheet_name='summary', index=False, header=False)
        df_roots.to_excel(writer, sheet_name='root folders', index=False)
        df_folders.to_excel(writer, sheet_name='all folders', index=False)
        df_files.to_excel(writer, sheet_name='files', index=False)
        df_extensions.to_excel(writer, sheet_name='filetypes', index=False)
else:
    df_summary.to_csv(write_path.name+'-summary.csv', index=False, header=False)
    df_roots.to_csv(write_path.name+'-rootfolders.csv', index=False)
    df_folders.to_csv(write_path.name+'-folders.csv', index=False)
    df_files.to_csv(write_path.name+'-files.csv', index=False)
    df_extensions.to_csv(write_path.name+'-filetypes.csv', index=False)

print('Done.\n')
print('read_path:', directory)
print('write_path:', write_path)
print('recent:', recent)
print('start:', start)
print('end:', end)
print('format:', output_format)
