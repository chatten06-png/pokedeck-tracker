import streamlit as st
import requests
import json
import os
from PIL import Image
import pytesseract

# --- (Keep your existing DATA_FILE, load_data, save_data, and fetch_card_data functions here) ---

# App Setup (Keep your existing setup and Create Deck sections)

elif choice == "Manage Deck":
    st.header("Search & Add Cards")
    if not decks:
        st.warning("Create a deck first!")
    else:
        deck_name = st.selectbox("Select Deck", list(decks.keys()))
        
        # Create tabs for Manual Search vs Camera Scan
        tab1, tab2 = st.tabs(["Manual Search", "📷 Scan Card"])
        
        with tab1:
            col1, col2 = st.columns([3, 1])
            with col1:
                search_query = st.text_input("Search Card Name (e.g., Charizard ex)")
            with col2:
                quantity = st.number_input("Quantity", min_value=1, max_value=4, value=1)
                
            if st.button("Search & Add"):
                with st.spinner("Searching database..."):
                    card_data = fetch_card_data(search_query)
                    if card_data:
                        decks[deck_name]["cards"].append({
                            "name": card_data["name"],
                            "type": card_data["supertype"],
                            "image": card_data["image"],
                            "quantity": quantity
                        })
                        save_data(decks)
                        st.success(f"Added {quantity}x {card_data['name']} to {deck_name}!")
                        st.image(card_data["image"], width=200)
                    else:
                        st.error("Card not found. Try checking your spelling.")

        with tab2:
            st.write("Use your phone camera to scan the **top half** of the card.")
            camera_image = st.camera_input("Take a picture of the card")
            
            if camera_image is not None:
                with st.spinner("Reading card text..."):
                    # Open the image using Pillow
                    img = Image.open(camera_image)
                    
                    # Crop the top 25% of the image to isolate the name and avoid body text
                    width, height = img.size
                    cropped_img = img.crop((0, 0, width, height * 0.25))
                    
                    # Extract text using Tesseract
                    extracted_text = pytesseract.image_to_string(cropped_img).strip()
                    
                    # Clean up the text (grab the first line, usually the name)
                    if extracted_text:
                        scanned_name = extracted_text.split('\n')[0]
                        st.info(f"**Scanned Name:** {scanned_name}")
                        
                        # Automatically search the API with the scanned name
                        card_data = fetch_card_data(scanned_name)
                        
                        if card_data:
                            st.image(card_data["image"], width=200)
                            if st.button(f"Add {card_data['name']} to Deck"):
                                decks[deck_name]["cards"].append({
                                    "name": card_data["name"],
                                    "type": card_data["supertype"],
                                    "image": card_data["image"],
                                    "quantity": 1
                                })
                                save_data(decks)
                                st.success(f"Added {card_data['name']} to {deck_name}!")
                        else:
                            st.warning("Could not find a match in the database. The scan might be slightly off due to glare.")
                    else:
                        st.error("Could not read any text. Try adjusting the lighting or reducing glare.")

# --- (Keep your existing View Decks section here) ---