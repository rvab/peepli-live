from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def make_circle_image(image_path, size, scale_factor=1.5):
    # Calculate new size (150% of the current size)
    new_size = (int(size[0] * scale_factor), int(size[1] * scale_factor))
    
    # Open the image file and resize it to 150% of the original size
    img = Image.open(image_path).resize(new_size, Image.Resampling.LANCZOS)
    
    # Create a circular mask with the new size
    mask = Image.new("L", new_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, new_size[0], new_size[1]), fill=255)
    
    # Apply the mask to make the image circular
    circular_img = ImageOps.fit(img, new_size, centering=(0.5, 0.5))
    circular_img.putalpha(mask)  # Apply transparency to the corners
    return circular_img

def draw_text_wrapped(draw, text, position, font, max_width):
    """Wrap the text and draw it within the specified width."""
    lines = textwrap.wrap(text, width=max_width)
    y_text = position[1]
    for line in lines:
        bbox = draw.textbbox((position[0], y_text), line, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        draw.text((position[0], y_text), line, font=font, fill="black")
        y_text += height + 10 # Add some spacing between lines
    return y_text # Return the updated y-coordinate

def render_card(team_wishes, employee_name, employee_img_path, output_path):
    # Load the template card (background image)

    # data_dir = os.path.join(BASE_DIR, 'data')
    # os.makedirs(data_dir, exist_ok=True)
    card = Image.open(os.path.join(BASE_DIR, 'card_template_1.jpg'))

    # Load, resize, and make the employee's profile picture round with 150% size
    employee_img = make_circle_image(employee_img_path, (400, 400), 2)

    # Paste the employee's circular image onto the card
    card.paste(employee_img, (100, 900), employee_img)

    # Initialize ImageDraw object
    draw = ImageDraw.Draw(card)

    # Choose fonts: regular, bold for names, and bold for anniversary message
    font_regular = ImageFont.truetype(os.path.join(BASE_DIR, "Lato-Regular.ttf"), 40)  # Regular font
    font_bold = ImageFont.truetype(os.path.join(BASE_DIR, "Lato-Bold.ttf"), 40)      # Bold font
    font_bold_large = ImageFont.truetype(os.path.join(BASE_DIR, "Pacifico-Regular.ttf"), 80)  # Bold font for anniversary message

    # Add employee's name and anniversary message (in bold and larger)
    draw.text((100, 1800), f"Happy Anniversary {employee_name}!", font=font_bold_large, fill="red")

    # Define the starting position, column width, and column margins
    y_position = 2000
    x_position = 100
    column_width = 700
    column_margin = 100
    max_y_position = 3500  # When to move to the next column

    # Add team member wishes with round profile pictures (scaled to 150%)
    for wish in team_wishes:
        # Load, resize, and make each team member's profile picture round and 150% larger
        team_img = make_circle_image(wish["profile_pic"], (160, 160))
        
        # Paste the circular profile picture of the team member
        card.paste(team_img, (x_position, y_position), team_img)
        
        # Add the team member's name in bold
        draw.text((x_position + 300, y_position + 10), f"{wish['name']}", font=font_bold, fill="black")
        
        # Add the team member's wish, wrapping it within the specified width (column width)
        y_position = draw_text_wrapped(draw, wish['wish'], (x_position + 300, y_position + 70), font_regular, max_width=column_width // 10)
        
        # Move down for the next entry
        y_position += 150
        
        # Check if the content exceeds the vertical limit, and move to the next column
        if y_position > max_y_position - 50:
            y_position = 2000  # Reset to the starting y position
            x_position += column_width + column_margin + 1000  # Move to the next column

    # Save the final card
    card.save(output_path, 'PNG')
    print(f"Card saved to: {output_path}")
