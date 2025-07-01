import csv
import os

print(f"Current working directory: {os.getcwd()}")

def load_pattern_data(file_path):
    # Initialize a dictionary to organize the data
    categories = {}

    # Open and read the CSV file
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category = row['category']
            forum = row['forum_name']
            post_title = row['title']  
            message = row['ravelry_link'].strip() if row['ravelry_link'] and row['ravelry_link'].strip() else "." # Ensure the message is never empty, fallback to a default value  

            # Add data to the dictionary
            if category not in categories:
                categories[category] = {}
            if forum not in categories[category]:
                categories[category][forum] = []
            categories[category][forum].append({
                "post_title": post_title,
                "message": message,
            })
    # Return the organized data
    return categories

