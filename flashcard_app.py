import pandas as pd
import streamlit as st
import os

# --- Configuration ---
CSV_FILE_NAME = "JP_3000.xlsx"
PROGRESS_FILE_NAME = "progress.txt" # New: File to store persistent progress
WORDS_PER_DAY = 10
COLUMN_JAPANESE = 'japanese'
COLUMN_PRONUNCIATION = 'pronunciation'
COLUMN_TRANSLATION = 'translation'
COLUMN_DAY = 'day'

# --- Helper Functions for Persistence ---

def load_progress(file_path):
    """
    Loads the last completed day from a text file.
    Returns 1 if the file doesn't exist or is invalid.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                day_str = f.read().strip()
                if day_str:
                    return int(day_str)
        except (ValueError, IOError) as e:
            st.warning(f"Could not read progress file or it's corrupted. Starting from Day 1. Error: {e}")
            return 1 # Fallback to Day 1 on error
    return 1 # Default to Day 1 if file doesn't exist

def save_progress(file_path, day_number):
    """
    Saves the current day to a text file.
    """
    try:
        with open(file_path, 'w') as f:
            f.write(str(day_number))
    except IOError as e:
        st.error(f"Could not save progress to file. Error: {e}")

# --- Helper Functions for Flashcards ---

@st.cache_data # Cache data loading to avoid re-reading the Excel on every rerun
def load_data(file_path):
    """
    Loads the flashcard data from an Excel file.
    Expects columns: 'japanese', 'pronunciation', 'translation', 'day'.
    """
    if not os.path.exists(file_path):
        st.error(f"Error: The file '{file_path}' was not found. Please ensure it's in the same directory as this script.")
        st.stop()

    df = pd.read_excel(file_path)

    required_columns = [COLUMN_JAPANESE, COLUMN_PRONUNCIATION, COLUMN_TRANSLATION, COLUMN_DAY]
    for col in required_columns:
        if col not in df.columns:
            st.error(f"Error: Missing required column '{col}' in your Excel file.")
            st.warning("Please ensure your Excel sheet has columns named 'japanese', 'pronunciation', 'translation', and 'day'.")
            st.stop()

    df = df.sort_values(by=COLUMN_DAY).reset_index(drop=True)
    return df

def get_words_for_day(df, day_number):
    """
    Filters the DataFrame to get WORDS_PER_DAY words for the specified day.
    """
    daily_words = df[df[COLUMN_DAY] == day_number]
    if daily_words.empty:
        return []
    return daily_words.head(WORDS_PER_DAY).to_dict(orient='records')

def display_card(card_data, show_translation):
    """
    Displays a single flashcard.
    """
    if not card_data:
        st.write("No card data available.")
        return

    st.markdown(
        """
        <style>
        .flashcard-container {
            border: 2px solid #4CAF50; /* Green border */
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background-color: #e8f5e9; /* Light green background */
            box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease-in-out;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
        }
        .flashcard-container:hover {
            box-shadow: 7px 7px 20px rgba(0,0,0,0.3);
            transform: translateY(-3px);
        }
        .flashcard-text {
            font-size: 2.5em; /* Larger font size */
            font-weight: bold;
            color: #2e7d32; /* Darker green for text */
            margin-bottom: 10px;
        }
        .flashcard-subtext {
            font-size: 1.5em; /* Medium font size */
            color: #388e3c; /* Medium green for subtext */
        }
        .button-group {
            display: flex;
            justify-content: space-between;
            width: 100%;
            margin-top: 20px;
        }
        .stButton button {
            background-color: #28a745; /* Bootstrap success green */
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 1em;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.2s ease;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            width: 100%; /* Ensure buttons take full width of their column */
        }
        .stButton button:hover {
            background-color: #218838; /* Darker green on hover */
            transform: translateY(-2px);
        }
        .stButton button:active {
            transform: translateY(0);
            box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    content_to_display = ""
    if show_translation:
        content_to_display = f"<div class='flashcard-text'>{card_data[COLUMN_TRANSLATION]}</div>"
    else:
        content_to_display = (
            f"<div class='flashcard-text'>{card_data[COLUMN_JAPANESE]}</div>"
            f"<div class='flashcard-subtext'>{card_data[COLUMN_PRONUNCIATION]}</div>"
        )

    st.markdown(f"<div class='flashcard-container' onclick='this.classList.toggle(\"flipped\")'>{content_to_display}</div>", unsafe_allow_html=True)


# --- Main Application Logic ---

def main():
    st.set_page_config(page_title="Japanese Flashcard App", layout="centered")

    st.title("🇯🇵 Japanese Flashcard App 📖")
    st.write("Learn 10 common Japanese words each day!")

    # Load data once
    df = load_data(CSV_FILE_NAME)
    total_max_day = df[COLUMN_DAY].max() if not df.empty else 0

    # Initialize session state variables if they don't exist
    # Load initial day from persistence file
    if 'current_day' not in st.session_state:
        st.session_state.current_day = load_progress(PROGRESS_FILE_NAME)
    if 'current_word_index' not in st.session_state:
        st.session_state.current_word_index = 0
    if 'show_translation' not in st.session_state:
        st.session_state.show_translation = False

    # Get words for the current day
    current_day_words = get_words_for_day(df, st.session_state.current_day)

    # --- Conditional Display of Cards or Day Completion ---
    if not current_day_words:
        st.info(f"You have completed all available words up to Day {total_max_day}! Great job!")
        # Save max day progress if all days are truly completed
        save_progress(PROGRESS_FILE_NAME, total_max_day)
        if st.button("Restart from Day 1"):
            st.session_state.current_day = 1
            st.session_state.current_word_index = 0
            st.session_state.show_translation = False
            save_progress(PROGRESS_FILE_NAME, st.session_state.current_day) # Save restart progress
            st.rerun()
        st.stop() # Stop further execution if no words for the day

    # Check if current_word_index is within bounds for displaying a card
    if st.session_state.current_word_index < len(current_day_words):
        # Display current day info
        st.markdown(f"### Day {st.session_state.current_day} - Word {st.session_state.current_word_index + 1} of {len(current_day_words)}")

        # Display the current flashcard
        current_card = current_day_words[st.session_state.current_word_index]
        display_card(current_card, st.session_state.show_translation)

        # --- Navigation Buttons (only shown if a card is being displayed) ---
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("⬅️ Back"):
                if st.session_state.current_word_index > 0:
                    st.session_state.current_word_index -= 1
                    st.session_state.show_translation = False # Reset flip state
                st.rerun()

        with col2:
            if st.button("🔄 Flip Card"):
                st.session_state.show_translation = not st.session_state.show_translation
                st.rerun()

        with col3:
            if st.button("Next ➡️"):
                if st.session_state.current_word_index < len(current_day_words) - 1:
                    st.session_state.current_word_index += 1
                    st.session_state.show_translation = False # Reset flip state
                else:
                    # User has finished the last flashcard of the day, prepare for next screen
                    st.session_state.current_word_index += 1 # Increment to trigger day completion state
                st.rerun()

    else:
        # User has completed the 10th flashcard of the day, show options
        next_day = st.session_state.current_day + 1
        st.markdown("<hr/>", unsafe_allow_html=True) # Separator
        st.success(f"🎉 You've completed Day {st.session_state.current_day}!")

        end_col1, end_col2 = st.columns(2)

        with end_col1:
            if st.button("🔄 Restart Day 1"):
                st.session_state.current_day = 1
                st.session_state.current_word_index = 0
                st.session_state.show_translation = False
                save_progress(PROGRESS_FILE_NAME, st.session_state.current_day) # Save restart progress
                st.rerun()

        with end_col2:
            if next_day <= total_max_day:
                if st.button(f"➡️ Go to Day {next_day}"):
                    st.session_state.current_day = next_day
                    st.session_state.current_word_index = 0
                    st.session_state.show_translation = False
                    save_progress(PROGRESS_FILE_NAME, st.session_state.current_day) # Save next day progress
                    st.rerun()
            else:
                st.info("You've completed all available days!")
                # Ensure the last completed day is saved even if it's the max
                save_progress(PROGRESS_FILE_NAME, total_max_day)
                if st.button("Restart from Day 1"):
                    st.session_state.current_day = 1
                    st.session_state.current_word_index = 0
                    st.session_state.show_translation = False
                    save_progress(PROGRESS_FILE_NAME, st.session_state.current_day) # Save restart progress
                    st.rerun()


if __name__ == "__main__":
    main()
