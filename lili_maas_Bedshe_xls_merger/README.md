# ZIP-to-Excel Azure Automation

This workflow automates the extraction and processing of ZIP file data sent via email.

## Flow

1. A ZIP file is sent to **anas.benabbou@dkm-customs.com**
2. The email is automatically **forwarded to an Azure Function**
3. The Azure Function:
   - Unzips the file
   - Extracts data from `.xls` and image via openAI
   - Performs required calculations
   - Generates a final **Excel report**
   - Returns the Excel file in the HTTP response
4. An **Azure Logic App** receives the response and sends the Excel file by email.

## Azure Function Code

The Azure Function is written in **Python** using `azure-functions`, `pandas`, `xlrd` and `openpyxl`. 
It handles file decoding, unzipping, data extraction (including `.xls`), and Excel generation inside the main HTTP trigger.


