# @Author: jwli.
# @Date  : 2024/04/16
import sys
import re
import pandas as pd
import pycountry

def extract_information(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print("File not found. Please check the path and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    records = [record for record in content.split('PMID')[1:] if record.strip()]
    data_list = []
    country_list = [country.name for country in pycountry.countries]
    country_aliases = {
        'UK': 'United Kingdom',
        'USA': 'United States',
        'Iran': 'Iran',
        'RU': 'Russia',
        'Czech Republic': 'Czech Republic',
        'Republic of Korea': 'Republic of Korea',
        'Netherlands': 'Netherlands',
        'Russia': 'Russia'
    }

    for record in records:
        lines = record.split('\n')
        data = {'PMID': '', 'Title': '', 'DOI': None, 'Abstract': '', 'Keywords': [], 'Publication Date': None, 'Authors': [], 'Country': None, 'Journal Title': ''}
        current_field = None
        address_lines = []

        for line in lines:
            if line.startswith('-'):
                data['PMID'] = line.split('-')[-1]
            elif line.startswith('TI  -'):
                current_field = 'Title'
                data[current_field] = line[5:].strip()
            elif line.startswith('AB  -'):
                current_field = 'Abstract'
                data[current_field] = line[5:].strip()
            elif line.startswith('JT  -'):
                current_field = 'Journal Title'
                data[current_field] = line[5:].strip()
            elif line.startswith('LID -') and '[doi]' in line:
                data['DOI'] = line[5:].split(' [')[0].strip()
                current_field = None
            elif line.startswith('OT  -'):
                data['Keywords'].append(line[5:].strip())
                current_field = None
            elif line.startswith('DP  -'):
                data['Publication Date'] = line[5:].strip()
                current_field = None
            elif line.startswith('AD  -'):
                current_field = 'Address'
                address_lines.append(line[5:].strip())
            elif line.startswith('AU  -'):
                data['Authors'].append(line[5:].strip())
                current_field = None
            elif line.startswith('      '):
                if current_field and current_field in data and current_field != 'Address':
                    data[current_field] += ' ' + line.strip()
                elif current_field == 'Address':
                    address_lines[-1] += ' ' + line.strip()
            else:
                current_field = None

        for address in address_lines:
            for country in country_list:
                if country in address:
                    data['Country'] = country
                    break
            if not data['Country']:
                for alias, actual_country in country_aliases.items():
                    if alias in address:
                        data['Country'] = actual_country
                        break
            if data['Country']:
                break

        if data['Keywords']:
            data['Keywords'] = ', '.join(data['Keywords'])
        if data['Authors']:
            data['Authors'] = ', '.join(data['Authors'])
        if data['PMID']:  # 如果 PMID 不为空，则将数据添加到列表中
            data_list.append(data)

    return pd.DataFrame(data_list)

def main(input_file, output_file):
    df = extract_information(input_file)
    df_cleaned = df.dropna(subset=['PMID'])
    df_cleaned.to_excel(output_file, index=False, engine='openpyxl')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_file_path> <output_file_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    main(input_path, output_path)
