import streamlit as st
import requests
import json
import os
from PIL import Image
import pytesseract

# --- Data Management ---
DATA_FILE = "decks.json"

def load_data():
    """Loads deck data from a local JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    """Saves deck data to a local JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def fetch_card_data(card_name):
    """Fetches card data from the Pokémon TCG API."""
    url = "https://api.pokemontcg.io/v2/cards"
    params = {"q": f'name:"{card_name}"'}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('data', [])
            if data:
                # Grab the first exact match
                card = data[0] 
                return {
                    "name": card.get("name"),
                    "supertype": card.get("supertype", "Unknown"),
                    "image": card.get("images", {}).get("small", ""),
                    "rules": card.get("rules", []) 
                }
        return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

# --- App Setup ---
st.set_page_config(page_title="PokéDeck Tracker Pro", page_icon="⚡", layout="wide")
st.title("⚡ PokéDeck Tracker Pro")

decks = load_data()

# --- Sidebar Navigation ---
menu = ["View Decks", "Create New Deck", "Manage Deck"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Create New Deck":
    st.header("Create a New Deck")
    deck_name = st.text_input("Deck Name (e.g., Charizard ex / Pidgeot)")
    format_type = st.selectbox("Format", ["Standard", "Expanded", "GLC", "Other"])
    
    if st.button("Create Deck"):
        if deck_name and deck_name not in decks:
            decks[deck_name] = {"format": format_type, "cards": []}
            save_data(decks)
            st.success(f"Deck '{deck_name}' created successfully!")
        elif deck_name in decks:
            st.error("A deck with this name already exists.")
        else:
            st.warning("Please enter a deck name.")

elif choice == "Manage Deck":
    st.header("Search & Add Cards")
    if not decks:
        st.warning("You need to create a deck first!")
    else:
        deck_name = st.selectbox("Select Deck", list(decks.keys()))
        
        # Tabs for Manual Search vs Camera Scan
        tab1, tab2 = st.tabs(["Manual Search", "📷 Scan Card"])
        
        with tab1:
            col1, col2 = st.columns([3, 1])
            with col1:
                search_query = st.text_input("Search Card Name (e.g., Charizard ex)")
            with col2:
                quantity = st.number_input("Quantity", min_value=1, max_value=4, value=1)
                
            if st.button("Search & Add to Deck"):
                with st.spinner("Searching the Pokémon TCG Database..."):
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
                        st.error("Card not found. Check your spelling and try again.")

        with tab2:
            st.write("Use your phone or webcam to scan the **top half** of the card.")
            camera_image = st.camera_input("Take a picture of the card")
            
            if camera_image is not None:
                with st.spinner("Reading card text..."):
                    img = Image.open(camera_image)
                    
                    # Crop the top 20% of the image to isolate the name
                    width, height = img.size
                    cropped_img = img.crop((0, 0, width, height * 0.20))
                    
                    # Extract text using Tesseract
                    extracted_text = pytesseract.image_to_string(cropped_img).strip()
                    
                    if extracted_text:
                        # Grab the first line, which is usually the name
                        scanned_name = extracted_text.split('\n')[0].strip()
                        st.info(f"**Scanned Name:** {scanned_name}")
                        
                        card_data = fetch_card_data(scanned_name)
                        
                        if card_data:
                            st.image(card_data["image"], width=200)
                            if st.button(f"Add 1x {card_data['name']} to Deck"):
                                decks[deck_name]["cards"].append({
                                    "name": card_data["name"],
                                    "type": card_data["supertype"],
                                    "image": card_data["image"],
                                    "quantity": 1
                                })
                                save_data(decks)
                                st.success(f"Added {card_data['name']} to {deck_name}!")
                        else:
                            st.warning("Could not find an exact match in the database. The scan might be slightly off due to glare.")
                    else:
                        st.error("Could not read any text. Try adjusting the lighting or reducing glare.")

elif choice == "View Decks":
    st.header("Your Decks")
    if not decks:
        st.info("No decks found. Go to the sidebar to create one!")
    else:
        deck_name = st.selectbox("Select a deck to view", list(decks.keys()))
        deck_info = decks[deck_name]
        
        st.subheader(deck_name)
        st.caption(f"**Format:** {deck_info['format']}")
        
        if not deck_info["cards"]:
            st.write("This deck is empty.")
        else:
            total_cards = sum(card['quantity'] for card in deck_info["cards"])
            
            # Progress bar for the 60-card limit
            st.progress(min(total_cards / 60.0, 1.0))
            
            if total_cards > 60:
                st.error(f"**Total Cards:** {total_cards}/60 (Illegal Deck Size)")
            elif total_cards == 60:
                st.success(f"**Total Cards:** {total_cards}/60 (Ready to Play!)")
            else:
                st.warning(f"**Total Cards: {total_cards}/60")
            
            st.write("---")
            
            # Display cards in a visual grid
            cols = st.columns(4)
            for index, card in enumerate(deck_info["cards"]):
                with cols[index % 4]:
                    st.image(card["image"], use_column_width=True)
                    st.markdown(f"x** {card['name']}")