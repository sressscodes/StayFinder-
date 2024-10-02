from flask import Flask, request, render_template
import os
import re
import random
from collections import defaultdict

app = Flask(__name__)

# Function to clean and tokenize the input text (removes punctuation and converts to lowercase)
def tokenize_text(text):
    return re.findall(r'\b\w+\b', text.lower())

# Function to load hotel data (documents) from the dataset folder
def load_hotel_data(folder_path):
    hotels = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            with open(os.path.join(folder_path, filename), 'r') as file:
                hotels[filename] = tokenize_text(file.read())
    return hotels

# Function to compute term frequencies and document frequencies for the hotel descriptions
def calculate_term_stats(hotels):
    hotel_count = len(hotels)
    term_doc_freq = defaultdict(int)  # Number of hotels containing each term
    term_freq = defaultdict(lambda: defaultdict(int))  # Term frequency in each hotel's description

    for hotel_id, words in hotels.items():
        unique_words = set(words)  # Unique words in each hotel's description
        for word in words:
            term_freq[hotel_id][word] += 1  # Counting term occurrences
        for word in unique_words:
            term_doc_freq[word] += 1  # Counting in how many hotel descriptions the term appears

    return term_freq, term_doc_freq, hotel_count

# Function to compute relevance scores using the Binary Independence Model (BIM)
def calculate_relevance_scores(query, term_freq, term_doc_freq, hotel_count):
    scores = {}
    for hotel_id in term_freq:
        score = 1.0  # Initialize the relevance score
        for term in query:
            term_frequency = term_freq[hotel_id].get(term, 0)
            doc_frequency = term_doc_freq.get(term, 0)
            # Probability of term being relevant for this hotel
            prob_term_relevant = (term_frequency + 1) / (sum(term_freq[hotel_id].values()) + len(term_doc_freq))
            # Probability of term being irrelevant for this hotel
            prob_term_irrelevant = (doc_frequency + 1) / (hotel_count - doc_frequency + len(term_doc_freq))
            # Updating score with BIM logic
            score *= (prob_term_relevant / prob_term_irrelevant)
        scores[hotel_id] = score
    return scores

# Main route for searching hotels based on user query
@app.route('/', methods=['GET', 'POST'])
def search_hotels():
    folder_path = 'dataset/Hotels of Nepal'  # Path to hotel data folder

    # Load the hotel descriptions (documents)
    hotel_data = load_hotel_data(folder_path)
    term_freq, term_doc_freq, hotel_count = calculate_term_stats(hotel_data)

    if request.method == 'POST':
        user_query = request.form['query']  # Get user's search query
        query_terms = tokenize_text(user_query)  # Tokenize the query
        scores = calculate_relevance_scores(query_terms, term_freq, term_doc_freq, hotel_count)
        # Rank the hotels based on their relevance scores
        ranked_hotels = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        # Select top 3 most relevant hotels to display
        top_hotels = [(hotel_id, round(score, 4)) for hotel_id, score in ranked_hotels[:5]]
        return render_template('results.html', query=user_query, results=top_hotels)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)