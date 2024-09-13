import requests

def download_image(url, save_path):
  # Send a GET request to the URL
  response = requests.get(url)
  
  # Check if the request was successful
  if response.status_code == 200:
    # Get the content of the response (the image data)
    image_data = response.content
    
    # Open a file in binary write mode and save the image data
    with open(save_path, 'wb') as file:
      file.write(image_data)

    print(f"Image successfully downloaded and saved to {save_path}")
  else:
    print(f"Failed to download image. Status code: {response.status_code}")
