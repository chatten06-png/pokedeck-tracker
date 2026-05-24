import streamlit as st
import requests
import json
import os

DATA_FILE = "decks.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def fetch_card_data(card_name):
    """Fetches card data from the Pokémon TCG API."""
    url = "https://api.pokemontcg.io/v2/cards"
    # Search for the exact name
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
                    "rules": card.get("rules", []) # Pulls exact text/rules if they exist
                }
        return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

# App Setup
st.set_page_config(page_title="PokéDeck Tracker Pro", page_icon="⚡", layout="wide")
st.title("⚡ PokéDeck Tracker Pro")

decks = load_data()

menu = ["View Decks", "Create New Deck", "Manage Deck"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Create New Deck":
    st.header("Create a New Deck")
    deck_name = st.text_input("Deck Name")
    format_type = st.selectbox("Format", ["Standard", "Expanded", "GLC", "Other"])
    
    if st.button("Create Deck"):
        if deck_name and deck_name not in decks:
            decks[deck_name] = {"format": format_type, "cards": []}
            save_data(decks)
            st.success(f"Deck '{deck_name}' created successfully!")
        elif deck_name in decks:
            st.error("A deck with this name already exists.")

elif choice == "Manage Deck":
    st.header("Search & Add Cards")
    if not decks:
        st.warning("Create a deck first!")
    else:
        deck_name = st.selectbox("Select Deck", list(decks.keys()))
        
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

elif choice == "View Decks":
    st.header("Your Decks")
    if not decks:
        st.info("No decks found.")
    else:
        deck_name = st.selectbox("Select a deck to view", list(decks.keys()))
        deck_info = decks[deck_name]
        
        st.subheader(deck_name)
        
        if not deck_info["cards"]:
            st.write("This deck is empty.")
        else:
            total_cards = sum(card['quantity'] for card in deck_info["cards"])
            st.progress(min(total_cards / 60.0, 1.0))
            st.caption(f"**Total Cards: {total_cards}/60")
            
            st.write("---")
            
            # Display cards in a visual grid
            cols = st.columns(4)
            for index, card in enumerate(deck_info["cards"]):
                # Rotate through columns to create a grid
                with cols[index % 4]:
                    st.image(card["image"], use_column_width=True)
                    st.markdown(f"x** {card['name']}")