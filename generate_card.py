import random

from datetime import date

from image_generator.script1 import render_card as render_card_1
from image_generator.script2 import render_card as render_card_2
from image_generator.script3 import render_card as render_card_3
from image_generator.helpers import download_image

from sqlite_helper import get_detailed_wishes_for_user, get_user_details


def generate_card_for_user(user_id):

  raw_wishes = get_detailed_wishes_for_user(user_id)
  print(f'Raw wishes: {raw_wishes}')
  wishes = []
  for wish in raw_wishes:
    save_path = wish[2].split('/')[-1] # Handle cases with no profile pic
    download_image(wish[2], save_path)

    wishes.append({
      "name": wish[1],
      "profile_pic": save_path,
      "wish": wish[3]
    })

  print(f'Wishes: {wishes}')

  for_user_details = get_user_details(user_id)
  print(f'For user details: {for_user_details}')
  for_user_name = for_user_details[0]
  for_user_profile_pic = for_user_details[2]

  save_path = for_user_profile_pic.split('/')[-1] # Handle cases with no profile pic
  download_image(for_user_profile_pic, save_path)

  today = date.today()
  output_card = f"{for_user_name}_{today}_card.jpg"
  print(f'Output card: {output_card}')

  renders = [render_card_1, render_card_2, render_card_3]

  # Choose a random option
  render_card = random.choice(renders)

  render_card(wishes, for_user_name, save_path, output_card)
  return output_card

# generate_card_for_user('UL9N5PX8V')
