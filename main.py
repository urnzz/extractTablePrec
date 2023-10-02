import os
import fitz  # PyMuPDF
from tqdm import tqdm
import re
import csv
from collections import defaultdict
from io import StringIO
final_patterns = {
    'E.P. Nº': r'(\d+/\d{4})',
    'Ordem Cronológica': r'(\d+/\d{4})',
    'Proc. DEPRE Nº': r'(\d+-\d+\.\d+\.\d+\.\d+\.0500)',
    'Nº de autos': r'(\d+-\d+\.\d+\.\d+\.\d+\.\d+)',
    'Vara': r'^(.*?Vara.*?)(?=\n)',
    'Advogado(s)': r'^(.*?\(OAB n°\d+\w+\))'
}

def extract_text_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    text = ''
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text += page.get_text("text")
    pdf_document.close()
    return text

def extract_info_from_block(block):
    extracted_info = extract_with_final_patterns(block)
    differentiated_ep_no_ordem_cronologica = differentiate_patterns(block, final_patterns['E.P. Nº'], final_patterns['Ordem Cronológica'], 'E.P. Nº', 'Ordem Cronológica')
    differentiated_n_de_autos_proc_depre_no = differentiate_patterns(block, final_patterns['Proc. DEPRE Nº'], final_patterns['Nº de autos'], 'Proc. DEPRE Nº', 'Nº de autos')
    
    # Merging the extracted information
    extracted_info.update(differentiated_ep_no_ordem_cronologica)
    extracted_info.update(differentiated_n_de_autos_proc_depre_no)
    return extracted_info

def extract_with_final_patterns(text):
    extracted_info = {}
    for key, pattern in final_patterns.items():
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            extracted_info[key] = match.group(1).strip()
        else:
            extracted_info[key] = ""
    return extracted_info

def differentiate_patterns(text, pattern1, pattern2, key1, key2):
    lines = text.split('\n')
    index1 = index2 = None
    for i, line in enumerate(lines):
        if re.match(pattern1, line):
            index1 = i
            break
    for i, line in enumerate(lines[index1+1:], start=index1+1):
        if re.match(pattern2, line):
            index2 = i
            break
    return {key1: lines[index1] if index1 is not None else "", key2: lines[index2] if index2 is not None else ""}


if __name__ == "__main__":
    input_folder = 'entrada'  # Change to your desired output folder
    
    if not os.path.exists(input_folder):
        print(f"Error: {input_folder} does not exist.")
        exit(1)

    
    # List all files in the 'entrada' folder
    files = os.listdir(input_folder)
    
    # Filter the list to include only PDF files
    pdf_files = [file for file in files if file.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {input_folder}.")
        exit(1)
    
    # Iterate over all PDF files and display a progress bar
    for pdf_file in tqdm(pdf_files, desc='Processing PDFs', unit='file'):
        pdf_path = os.path.join(input_folder, pdf_file)
        
        extracted_text = extract_text_from_pdf(pdf_path)
        # Split the text into blocks using "Advogado(s):" as the delimiter
        blocks = re.split(r'Advogado\(s\):', extracted_text)
        blocks = ['Advogado(s):' + block for block in blocks if block.strip()]
        # Extract information from each block and write to CSV
        output_file_path = 'otp.csv'  # Replace with your desired output file path
        headers = list(final_patterns.keys())
        with open(output_file_path, 'w', newline='') as csvfile:
            csv_writer = csv.DictWriter(csvfile, fieldnames=headers)
            csv_writer.writeheader()
            for block in blocks:
                extracted_info = extract_info_from_block(block)
                csv_writer.writerow(extracted_info)
