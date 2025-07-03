import csv

# Function to load data from CSV file
def load_pattern_data(file_path):
    # Initialize a dictionary to organize the data
    categories = {}

    # Open and read the CSV file
    
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category = row['Category']
            forum = row['Forum Name']
            post_title = row['Title']  
            message = row['Ravelry Link/Message'].strip() if row['Ravelry Link/Message'] and row['Ravelry Link/Message'].strip() else "." # Ensure the message is never empty, fallback to a default value  
            post_tags = [tag.strip() for tag in row['Tags'].split(',')] if row['Tags'] else []
            catbox_link = row['Catbox link'].strip() if row['Catbox link'] else None


            # Add data to the dictionary
            if category not in categories:
                categories[category] = {}
            if forum not in categories[category]:
                categories[category][forum] = []
            categories[category][forum].append({
                "post_title": post_title,
                "message": message,
                "tags": post_tags,
                "catbox_link": catbox_link
            })
    # Return the organized data
    return categories