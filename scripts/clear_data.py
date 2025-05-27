import os

directory = "data"  # change this to your target directory
keep_file = "reddit_data.csv"

for filename in os.listdir(directory):
    file_path = os.path.join(directory, filename)

    if filename == keep_file:
        continue

    if os.path.isfile(file_path):
        os.remove(file_path)
        print(f"Deleted: {filename}")
