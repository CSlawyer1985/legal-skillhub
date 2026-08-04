# -*- coding: utf-8 -*-
import os
import sys

input_dir = r'C:\Users\yangy\.openclaw\workspace\contract-diff\input'
output_dir = r'C:\Users\yangy\.openclaw\workspace\contract-diff\output'

files = os.listdir(input_dir)
print("Input files:")
for f in files:
    full_path = os.path.join(input_dir, f)
    print(f"  {f!r}")
    
# Show the Python repr so we can see exact bytes
docx_file = [f for f in files if f.endswith('.docx')][0]
pdf_file = [f for f in files if f.endswith('.pdf')][0]

print(f"\nUsing: {docx_file!r}")
print(f"Using: {pdf_file!r}")

# Copy files to simple names
import shutil
shutil.copy(os.path.join(input_dir, docx_file), os.path.join(input_dir, 'template.docx'))
shutil.copy(os.path.join(input_dir, pdf_file), os.path.join(input_dir, 'scanned.pdf'))

print("\nFiles copied to template.docx and scanned.pdf")