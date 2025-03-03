from printServices import *
import re
import streamlit as st


def read_barcode(barcode):
    match = re.search(r'id¡(\d+)', barcode)
    if match:
        id_value = match.group(1)
        st.session_state['attendee_id'] = id_value
        return id_value
    else:
        return None


def on_barcode_scan(printer_type):
    barcode = read_barcode(st.session_state.barcode_input)
    if barcode:  # If barcode processing is successful
        check_accredited(st.session_state['attendee_id'])
        print_ticket(barcode, printer_type)
        st.session_state.barcode_input = ""



