from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
from airtableRequests import *
import streamlit as st
# ExampleBarcodeid¡1170296MoreText

a6_width_pixels, a6_height_pixels = int(4.1 * 300), int(5.8 * 300)
# Load api details
with open('config.json', 'r') as config_file:
    font_path = config['Font_Path']
    Group_Ids_Without_Company = config['Group_Ids_Without_Company']


def create_and_print_image(firstname, lastname, company, group_id, printer_type):
    image = Image.new('RGB', (a6_width_pixels, a6_height_pixels), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Fixed font sizes
    font_size_names = 73
    font_size_company = 42

    if len(firstname) > 14 or len(lastname) > 14:
        font_size_names = 63
    if len(firstname) > 16 or len(lastname) > 16:
        font_size_names = 59
    if len(firstname) > 18 or len(lastname) > 18:
        font_size_names = 55
    if company:
        if len(company) > 17:
            font_size_company = 35

    # Load fonts
    font_names = ImageFont.truetype(font_path, font_size_names)
    font_company = ImageFont.truetype(font_path, font_size_company)

    # Calculate starting y position based on the desired bottom margin
    bottom_margin = 985
    starting_y_position = a6_height_pixels - bottom_margin

    # Adjust for printer type
    if printer_type == 'HP':
        y_position_first_name_adjustment = 285
        left_shift = 325
    elif printer_type == 'Samsung':
        y_position_first_name_adjustment = 250
        left_shift = 0

    # Apply coordinates adjustments for printing
    y_position_first_name = starting_y_position - y_position_first_name_adjustment
    y_position_last_name = y_position_first_name + 80
    y_position_company = y_position_last_name + 130

    # Centering text
    # Calculate centered x-coordinate for each text
    x_coordinate_first_name, _ = center_text_position(firstname, font_names, draw, y_position_first_name, left_shift)
    x_coordinate_last_name, _ = center_text_position(lastname, font_names, draw, y_position_last_name, left_shift)
    if company and group_id not in Group_Ids_Without_Company:
        x_coordinate_company, _ = center_text_position(company, font_company, draw, y_position_company, left_shift)

    # Drawing centered text
    draw.text((x_coordinate_first_name, y_position_first_name), firstname, font=font_names, fill=(0, 0, 0))
    draw.text((x_coordinate_last_name, y_position_last_name), lastname, font=font_names, fill=(0, 0, 0))
    if company and group_id not in Group_Ids_Without_Company:
        draw.text((x_coordinate_company, y_position_company), company, font=font_company, fill=(0, 0, 0))

    # Save and print the image
    temp_image_path = 'temp_ticket.png'
    image.save(temp_image_path)
    print_image(temp_image_path)
    os.remove(temp_image_path)


def center_text_position(text, font, draw, y, x_shift):
    # Calculate the position to center the text
    text_bbox = draw.textbbox((0, 0), text, font)
    text_width = text_bbox[2] - text_bbox[0]
    x = (a6_width_pixels - text_width) / 2
    return x - x_shift, y


def print_image(image_path):
    # Print the image using the lpr command
    try:
        subprocess.run(["lpr", image_path], check=True)
    except subprocess.CalledProcessError as e:
        st.write(f"Failed to print. Error: {e}")
    except Exception as e:
        st.write(f"An unexpected error occurred: {e}")


def print_ticket(attendee_id, printer_type):
    first_name = get_attendee_field_info(attendee_id, 'Firstname')
    last_name = get_attendee_field_info(attendee_id, 'Lastname')
    company = get_attendee_field_info(attendee_id, 'Company')
    group_id = get_attendee_field_info(attendee_id, 'GroupId')
    check_station = check_id_in_station(group_id, st.session_state['station_type'])

    if not check_station:
        st.session_state['wrong_station'] = True

    if (st.session_state['action_taken'] or check_station) and st.session_state['already_accredited'] is False:
        # Proceed with the rest only if allowed or after pressing "Continue Anyway"
        try:
            group_id_name = get_group_id_name(group_id)
            st.info(f'Printing ticket for: {first_name} {last_name}, Company: {company}, Group: {group_id_name}, Group ID: {group_id}')
            create_and_print_image(first_name, last_name, company, group_id, printer_type)
            print_attendee_info(attendee_id)
            st.success("Ticket print job sent successfully.")
            update_accredited_date(attendee_id)
            log_accreditation(attendee_id)
        except Exception as e:
            st.error(f"Error while printing ticket: {e}")
            st.session_state['action_taken'] = False
        finally:
            st.session_state['attendee_id'] = ""
            st.session_state['action_taken'] = False
            st.session_state['wrong_station'] = False
            st.session_state['already_accredited'] = False

def manual_print(printer_type):
    api, base, users_table = initialize_table(AccreditationUserTable)

    query_formula = f"{{Username}}='PRINT_MANUALLY'"
    records = users_table.all(formula=query_formula)
    PRINT_PASSWORD = records[0]['fields'].get('Password')

    is_master = 'user_role' in st.session_state and st.session_state['user_role'] == "Master"
    is_supporter = 'user_role' in st.session_state and st.session_state['user_role'] == "Supporter"
    access_granted = False

    if is_master:
        access_granted = True
    elif is_supporter:
        # Prompt for password if the user is a Supporter
        if 'password_correct' not in st.session_state:
            st.session_state['password_correct'] = False
        supporter_password = st.text_input("Enter access password:", type="password", key='supporter_access_password',
                                           placeholder='Access denied: Ask your supervisor for the password!')
        if supporter_password:
            if supporter_password == PRINT_PASSWORD:
                access_granted = True
                st.session_state['password_correct'] = True
                st.success("Access granted.")
            else:
                st.error("Access denied: Incorrect password.")
    if access_granted:
        first_name = st.text_input("Enter first name")
        last_name = st.text_input("Enter last name")
        company_name = st.text_input("Enter company name")
        group_id = 00000

        print_button = st.button("Print")
        if print_button:
            create_and_print_image(first_name, last_name, company_name, group_id,printer_type)

