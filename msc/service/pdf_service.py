import fitz
import json
import re

def is_container_number(text):
    pattern = r"^[A-Za-z]{4}\d{7}$"
    return bool(re.match(pattern, text))

def extract_text_from_coordinates(pdf_path, coordinates, key_map):
    pdf_document = fitz.open(pdf_path)
    extracted_text = {}

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        page_text = []

        for (x0, y0, x1, y1) in coordinates:
            rect = fitz.Rect(x0, y0, x1, y1)
            text = page.get_text("text", clip=rect)
            page_text.append(text.strip())

        extracted_text[page_num + 1] = page_text

    if len(extracted_text[1]) != len(key_map):
        raise ValueError("Length of data list and key map must be equal.")

    data_dict = dict(zip(key_map, extracted_text[1]))
    return json.dumps(data_dict)

def process(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
    except Exception as e:
        raise ValueError(f"Failed to open PDF file: {e}")

    extracted_data = []  # List to store containers and their items
    container_coords = (60, 320, 130, 328)

    item_coords = [
        (90, 340, 130, 348),  # Item check coords
        (150, 340, 210, 348),
        (210, 333, 310, 348),
        (450, 333, 550, 348),
    ]

    cy_increment = 30  # Increment for container y-axis after finding each container
    y_increment = 13   # Increment for items' y-axis to search next row of items

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        cx0, cy0, cx1, cy1 = container_coords

        while True:
            # Check for container
            rect = fitz.Rect(cx0, cy0, cx1, cy1)
            container_text = page.get_text("text", clip=rect).strip()

            if is_container_number(container_text):
                container_data = {
                    "container": container_text,
                    "items": []
                }

                # Adjust item coordinates based on container's y position
                container_y_offset = cy0 - container_coords[1]
                new_coords = [(x0, y0 + container_y_offset, x1, y1 + container_y_offset) for (x0, y0, x1, y1) in item_coords]

                attempts = 0  # Counter to track the number of consecutive empty checks
                while attempts < 2:  # Double check if the text is empty twice
                    temp_items = []
                    found_text = False

                    # Extract all coordinates for the items
                    for (x0, y0, x1, y1) in new_coords:
                        rect = fitz.Rect(x0, y0, x1, y1)
                        item_text = page.get_text("text", clip=rect).strip()

                        if item_text:  # Check if text is not empty
                            temp_items.append(item_text)
                            found_text = True
                        else:
                            found_text = False
                            break  # Stop if any item field is missing

                    # Append the item data if valid items are found
                    if len(temp_items) == 4:
                        item_data = {
                            "item": temp_items[0],       # Item identifier
                            "pkgs": temp_items[1],       # Package info
                            "desc": temp_items[2],       # Description
                            "weight": temp_items[3]      # Weight
                        }
                        container_data["items"].append(item_data)

                    # Break if no text was found twice in a row
                    if not found_text:
                        attempts += 1
                    else:
                        # Increment the y-axis for the next set of items
                        new_coords = [(x0, y0 + y_increment, x1, y1 + y_increment) for (x0, y0, x1, y1) in new_coords]
                        attempts = 0  # Reset attempts if text was found

                # Append the container data (with its items) to the final result
                extracted_data.append(container_data)

            # Increment the y-axis for the container for the next attempt
            cy0 += cy_increment
            cy1 += cy_increment

            # Check if there are more containers to extract, otherwise break
            next_rect = fitz.Rect(cx0, cy0, cx1, cy1)
            next_container_text = page.get_text("text", clip=next_rect).strip()
            if not next_container_text:
                break

    return extracted_data