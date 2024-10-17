import fitz  # PyMuPDF
import re
import json

def extract_text_from_pdf(pdf_path, coordinates_page_2, coordinates_2, key_map=None):
    if key_map is None:
        key_map = ["Vissel", "Stay", "Loyds", "BL Number", "Origin Country", "Description"]

    pdf_document = fitz.open(pdf_path)
    
    # Ensure the PDF has at least 3 pages
    if len(pdf_document) < 3:
        raise ValueError("The PDF must have at least 3 pages.")
    
    # Select page 2 (index 1 because pages are 0-based in PyMuPDF)
    page_2 = pdf_document[1]
    results = []  # List to hold all container data
    container_count = 0  # Track number of containers
    
    # Extract static data from page 2
    static_data = {}
    for i, (x0, y0, x1, y1) in enumerate(coordinates_page_2[:6]):
        rect = fitz.Rect(x0, y0, x1, y1)
        static_data[key_map[i]] = page_2.get_text("text", clip=rect).strip()
    
    # Extract text for Container, Packages, Article from page 2 with dynamic Y-axis increment
    container_index = 6  # Start index for container-related coordinates
    y_increment = 10
    y_offset = 0  # Offset to increment for multiple rows of container data
    
    while True:
        # Extract container
        rect = fitz.Rect(coordinates_page_2[container_index][0], coordinates_page_2[container_index][1] + y_offset,
                         coordinates_page_2[container_index][2], coordinates_page_2[container_index][3] + y_offset)
        container = page_2.get_text("text", clip=rect).strip()

        # Extract packages
        rect = fitz.Rect(coordinates_page_2[container_index+1][0], coordinates_page_2[container_index+1][1] + y_offset,
                         coordinates_page_2[container_index+1][2], coordinates_page_2[container_index+1][3] + y_offset)
        packages = page_2.get_text("text", clip=rect).strip()

        # Extract article
        rect = fitz.Rect(coordinates_page_2[container_index+2][0], coordinates_page_2[container_index+2][1] + y_offset,
                         coordinates_page_2[container_index+2][2], coordinates_page_2[container_index+2][3] + y_offset)
        article = page_2.get_text("text", clip=rect).strip()

        # Validate container format (4 letters + 7 digits)
        container_valid = bool(re.match(r"^[A-Z]{4}\d{7}$", container))
        packages_valid = packages.isdigit()
        article_valid = article.isdigit()

        if container_valid and packages_valid and article_valid:
            # Valid data found, increment the container count and create a new entry
            container_count += 1
            item_data = {
                "item": 1,
                "Packages": int(packages),
                "Net Weight": 0,  # Always 0
                "Gross Weight": None,  # To be filled later if applicable
                "Description": static_data.get("Description", "")
            }

            container_data = {
                "vissel": static_data.get("Vissel", ""),
                "container": container,
                "dispatch_country": static_data.get("Origin Country", ""),
                "Quay": 1700,  # Always 1700
                "Stay": int(static_data.get("Stay", 0)),
                "LoydsNumber": static_data.get("Loyds", ""),
                "Article": int(article),
                "items": [item_data]
            }

            results.append(container_data)  # Add container data to results
            
            # Increase y_offset for next row
            y_offset += y_increment
        else:
            break  # Stop if no more valid data is found

    # If only one container, extract Gross Weight from page 2
    if container_count == 1:
        rect = fitz.Rect(coordinates_page_2[9][0], coordinates_page_2[9][1], coordinates_page_2[9][2], coordinates_page_2[9][3])
        gross_weight = page_2.get_text("text", clip=rect).strip()
        if gross_weight:
            results[0]["items"][0]["Gross Weight"] = float(gross_weight)

    # Extract data from pages 3 to the end
    for page_num in range(2, len(pdf_document)):
        page = pdf_document[page_num]
        container_count = 0
        y_offset = 0  # Reset y_offset for each page

        while True:
            # Extract container from page n
            rect = fitz.Rect(coordinates_2[3][0], coordinates_2[3][1] + y_offset,
                             coordinates_2[3][2], coordinates_2[3][3] + y_offset)
            container = page.get_text("text", clip=rect).strip()

            # Extract packages from page n
            rect = fitz.Rect(coordinates_2[4][0], coordinates_2[4][1] + y_offset,
                             coordinates_2[4][2], coordinates_2[4][3] + y_offset)
            packages = page.get_text("text", clip=rect).strip()

            # Extract article from page n
            rect = fitz.Rect(coordinates_2[5][0], coordinates_2[5][1] + y_offset,
                             coordinates_2[5][2], coordinates_2[5][3] + y_offset)
            article = page.get_text("text", clip=rect).strip()

            # Validate container format (4 letters + 7 digits)
            container_valid = bool(re.match(r"^[A-Z]{4}\d{7}$", container))
            packages_valid = packages.isdigit()
            article_valid = article.isdigit()

            if container_valid and packages_valid and article_valid:
                # Valid data found, increment the container count and create a new entry
                container_count += 1
                item_data = {
                    "item": 1,
                    "Packages": int(packages),
                    "Net Weight": 0,  # Always 0
                    "Gross Weight": None,  # To be filled later if applicable
                    "Description": page.get_text("text", clip=fitz.Rect(coordinates_2[2][0], coordinates_2[2][1],
                                                                        coordinates_2[2][2], coordinates_2[2][3])).strip()
                }

                container_data = {
                    "vissel": static_data.get("Vissel", ""),
                    "container": container,
                    "dispatch_country": page.get_text("text", clip=fitz.Rect(coordinates_2[1][0], coordinates_2[1][1],
                                                                            coordinates_2[1][2], coordinates_2[1][3])).strip(),
                    "Quay": 1700,  # Always 1700
                    "Stay": int(static_data.get("Stay", 0)),
                    "LoydsNumber": static_data.get("Loyds", ""),
                    "Article": int(article),
                    "items": [item_data]
                }

                results.append(container_data)  # Add container data to results

                # Increase y_offset for next row
                y_offset += y_increment
            else:
                break  # Stop if no more valid data is found

        # If only one container on this page, extract Gross Weight
        if container_count == 1:
            rect = fitz.Rect(coordinates_2[6][0], coordinates_2[6][1], coordinates_2[6][2], coordinates_2[6][3])
            gross_weight = page.get_text("text", clip=rect).strip()
            if gross_weight:
                results[-1]["items"][0]["Gross Weight"] = float(gross_weight)

    # Return results as a JSON string
    return json.dumps(results, indent=2)

def extract_text_from_pages(pdf_path, coordinates, key_map=["BL Number", "Origin Country", "Description", "container", "packages", "article", "Gross Weight"]):
    pdf_document = fitz.open(pdf_path)
    
    # Ensure the PDF has at least 2 pages
    if len(pdf_document) < 2:
        raise ValueError("The PDF must have at least 2 pages.")
    
    all_page_data = []

    # Loop through pages starting from page 2 (index 1 because pages are 0-based)
    for page_num in range(1, len(pdf_document)):
        page = pdf_document[page_num]
        page_text = []

        # Extract text from specific coordinates
        for (x0, y0, x1, y1) in coordinates:
            rect = fitz.Rect(x0, y0, x1, y1)
            text = page.get_text("text", clip=rect)
            page_text.append(text.strip())

        # Check if the number of extracted texts matches the number of keys in the key_map
        if len(page_text) != len(key_map):
            raise ValueError(f"Length of data list and key map must be equal on page {page_num + 1}.")

        # Map the extracted text to the provided key_map and append the result to the list
        data_dict = dict(zip(key_map, page_text))
        all_page_data.append({
            "page": page_num + 1,  # Store the page number (1-based index)
            "data": data_dict
        })

    return json.dumps(all_page_data, indent=2)