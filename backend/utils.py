import os
from datetime import date

def clear_and_ensure_folder(folder_path):
    """Clear all files in the specified folder and create the folder if it doesn't exist."""
    # Check if the folder exists
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)  # Create the folder if it doesn't exist
    else:
        # If the folder exists, remove all files inside it
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass  # Skip if the file does not exist



def calculate_centered_roi(screen_width, screen_height, roi_width_percent=0.7, roi_height_percent=0.7):
    roi_width = int(screen_width * roi_width_percent)
    roi_height = int(screen_height * roi_height_percent)
    roi_x = (screen_width - roi_width) // 2
    roi_y = (screen_height - roi_height) // 2
    
    return roi_x, roi_y, roi_width, roi_height

