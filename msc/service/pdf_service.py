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

    for page_num in range(len(pdf_document)):

        page = pdf_document[page_num]
        attempts = 0
        cy_increment = 30  # Adjust the increment as needed
        y_increment = 13  # Adjust the increment as needed

        cx0, cy0, cx1, cy1 = container_coords
        while True:
            # Check for container
            rect = fitz.Rect(cx0, cy0, cx1, cy1)
            text = page.get_text("text", clip=rect).strip()

            if is_container_number(text):
                container_data = {
                    "container": text,
                    "items": []
                }

                found_text = False  # Flag to track if text is found
                attempts = 0  # Counter to track the number of consecutive empty checks
                new_coords = list(item_coords)

                while attempts < 2:  # Double check if the text is empty twice
                    temp_items = []

                    # Extract all coordinates for the items
                    for (x0, y0, x1, y1) in new_coords:
                        rect = fitz.Rect(x0, y0, x1, y1)
                        text = page.get_text("text", clip=rect).strip()

                        if text:  # Check if text is not empty
                            temp_items.append(text)
                            found_text = True
                        else:
                            found_text = False

                    # Append the item data if found
                    if found_text:
                        item_data = {
                                "item": temp_items[0],       # Here 'text' is the item's identifier, change if needed
                                "pkgs": temp_items[1],         # Assign appropriate extracted values for pkgs, desc, weight
                                "desc": temp_items[2],
                                "weight": temp_items[3]
                        }
                        container_data["items"].append(item_data)

                    # Stop processing further coordinates if no text was found after two attempts
                    if not found_text and attempts >= 2:
                        break
                    elif not found_text:
                        attempts += 1
                    else:
                        # Increment the y-axis for the next attempt
                        new_coords = [(x0, y0 + y_increment, x1, y1 + y_increment) for (x0, y0, x1, y1) in new_coords]

                # Append the container data (with its items) to the final result
                extracted_data.append(container_data)
            else:
                break

            # Increment the y-axis for the container for the next attempt
            cy0 += cy_increment
            cy1 += cy_increment

    return extracted_data

