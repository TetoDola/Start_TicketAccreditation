from barcodeScanning import *
from printServices import *
from airtableRequests import *
import streamlit as st

# Default session state aka when it launches
default_session_state = {
    'is_logged_in': False,
    'user_role': None,
    'status_message': "",
    'station_type': "",
    'barcode_input': "",
    'wrong_station': False,
    'attendee_id': False,
    'action_taken': False,
    'already_accredited': False
}

for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.title("START Global - Ticket Accreditation")

# Handle login/logout
if not st.session_state.is_logged_in:
    with st.container():
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            # login function in streamlit returns a Bool + a Status message
            st.session_state.is_logged_in, st.session_state.status_message = login(username, password)
            st.rerun()
else:
    # Show logout button if user is logged in
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button('Logout'):
            logout()
            st.rerun()

# Display status messages
if st.session_state.status_message:
    st.info(st.session_state.status_message)
    st.session_state.status_message = ""

# Custom CSS for idk what, prolly spacing. Idk CSS so i wont touch this shit
st.markdown(
    "<style>.stRadio > div{margin-bottom: 20px;}</style>",
    unsafe_allow_html=True
)

# Main UI - also not me who did it so i wont touch this. Again idk UI -_- Fuck UI
if st.session_state.is_logged_in:
    st.markdown("<br>", unsafe_allow_html=True)

    # Select printer before defining functions to make it available in all functions
    printer_type = st.selectbox('Select Printer Type', ['HP', 'Samsung'])


    # Define functions for each feature option
    def scan_and_print():
        st.text_input('Scan a barcode:', value="", key='barcode_input', on_change=lambda: on_barcode_scan(printer_type))


    def change_station():
        station_types = get_station_types()
        current_index = station_types.index(
            st.session_state.station_type) if st.session_state.station_type in station_types else 0
        new_station_type = st.selectbox("Select Station Type", station_types, index=current_index)

        if new_station_type != st.session_state.get('station_type', ''):
            st.session_state.station_type = new_station_type
            st.info(f'Station changed to: {new_station_type}')
            st.info(f"Allowed Group_Id's: {load_allowed_ids(new_station_type)}")


    def print_specific_ticket():
        attendee_id_input, barcode_scan_input = st.columns(2)
        with attendee_id_input:
            st.session_state.attendee_id = st.text_input("Enter the attendee's ID", key='attendee_id_direct')
        with barcode_scan_input:
            barcode_input = st.text_input('Scan a barcode', key='barcode_input_scan')

        if st.button("Print Ticket"):
            if st.session_state.attendee_id:
                check_accredited(st.session_state.attendee_id)
                print_ticket(st.session_state.attendee_id, printer_type)
            elif barcode_input:
                barcode = read_barcode(barcode_input)
                if barcode:
                    check_accredited(barcode)
                    print_ticket(barcode, printer_type)
                else:
                    st.error("Invalid barcode.")
            else:
                st.error("Please enter an attendee ID or scan a barcode.")

    #ehhhhhhh what's going on here???
    def handle_manual_print():
        manual_print(printer_type)


    # Map options to their respective functions
    options = {
        "Scan and Print Ticket": scan_and_print,
        "Change Station Type": change_station,
        "Print specific attendee's ticket - Info desk": print_specific_ticket,
        "AirTable Data / Look for Attendee": print_airtable_data,
        "Create new Attendee": create_new_attendee,
        "Manual Print": handle_manual_print
    }

    # Show option selection and execute selected function
    selected_option = st.radio("Select an option", list(options.keys()))
    st.markdown("<br>", unsafe_allow_html=True)

    # Call the function associated with the selected option
    options[selected_option]()

    if st.session_state.wrong_station or st.session_state.already_accredited:
        st.info("If you want to continue, press the Continue Anyway button, otherwise Abort.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Continue Anyway"):
                st.session_state.wrong_station = False
                st.session_state.action_taken = True
                st.session_state.already_accredited = False
                print_ticket(st.session_state.attendee_id, printer_type)
                st.rerun()

        with col2:
            if st.button("Abort"):
                st.session_state.wrong_station = False
                st.error("Aborting. The ticket will not be printed.")
                st.rerun()