import os
import xml.etree.ElementTree as ET
from PIL import Image

def crop_images(image_folder, xml_folder, output_folder):
    for xml_file in os.listdir(xml_folder):
        if not xml_file.endswith('.xml'):
            continue

        # Parse XML file
        tree = ET.parse(os.path.join(xml_folder, xml_file))
        root = tree.getroot()

        # Get filename and load the image
        filename = root.find('filename').text.replace(" ", "")  # Replace spaces with escaped spaces
        image_path = os.path.join(image_folder, filename)
        try:
            img = Image.open(image_path)
        except FileNotFoundError:
            print(f"File not found: {image_path}")
            continue

        for obj in root.findall('object'):
            bndbox = obj.find('bndbox')
            if bndbox is None:
                print(f"Warning: 'bndbox' missing in {xml_file} for object {obj.find('name').text}")
                continue
            
            # Get label and coordinates
            label = obj.find('name').text
            xmin = int(bndbox.find('xmin').text)
            ymin = int(bndbox.find('ymin').text)
            xmax = int(bndbox.find('xmax').text)
            ymax = int(bndbox.find('ymax').text)

            # Crop and save
            cropped_img = img.crop((xmin, ymin, xmax, ymax))
            if cropped_img.mode in ['RGBA', 'P']:
                cropped_img = cropped_img.convert("RGB")
            save_path = os.path.join(output_folder, f"{filename.split('.')[0]}_{label}.jpg")
            cropped_img.save(save_path)



# Directory paths for your images and xml files, and where you want to save cropped images
image_folder = 'data/salat/a_Salat-All-img-xml'
xml_folder = 'data/salat/a_Salat-All-img-xml'
output_folder = 'data/salat/a_Salat-All-img-xml_'

# Create output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

crop_images(image_folder, xml_folder, output_folder)
