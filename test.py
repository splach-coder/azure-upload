import zipfile

# Initialize a list to store extracted PDFs
pdf_files = []
zip_bytes = "./files/5742967 DKM.zip"

# Unzip the file
with zipfile.ZipFile(zip_bytes, 'r') as zip_ref:
    for file in zip_ref.namelist():
        # Check if the file is a PDF
        if file.endswith('.pdf'):
            with zip_ref.open(file) as pdf_file:
                pdf_content = pdf_file.read()
                pdf_files.append((file, pdf_content))
# Do further processing with the PDF files
# For example, log the names of the PDFs found:
for file_name, pdf_data in pdf_files:
    print(f"Extracted PDF: {file_name}")