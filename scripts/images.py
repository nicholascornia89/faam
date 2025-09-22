"""
This scripts is going to convert programmatically 
all images stored in the FAAM GitHub repositories and convert them to Webp
"""

# Dedicated libraries
# from PIL import Image
import pyvips
from glob import glob
from pathlib import Path
from multiprocessing import Pool


# local scripts
import sys

sys.path.append(".")
from utilities import *

# Repositories

working_dir = os.path.join("tmp", "images_to_be_processed")


def convert_directories(quality=10):
    for d in os.listdir(working_dir):
        print(f"Converting images in {d} directory...")
        for f in os.listdir(os.path.join(working_dir, d, "images")):
            print(f"Current file: {f}")
            start_time = datetime.datetime.now()
            img = pyvips.Image.new_from_file(
                os.path.join(working_dir, d, "images", f), access="sequential"
            )
            filename = f.replace(".jpg", ".webp")
            img.write_to_file(os.path.join(working_dir, d, filename), Q=quality)

            end_time = datetime.datetime.now()
            diff = end_time - start_time
            print(f"Time taken: {diff.seconds} s")

        """ remove previous images
        for f in os.listdir(os.path.join(working_dir, d, "images")):
            os.remove(f)
        """


### CODE ###

# convert_directories()


def conversion_file(f, quality=10, treshold=10000):
    # check image size, webp treshold 16383x16383 pixels
    if os.stat(f).st_size > treshold:
        # print(f"Need to resize {f} first...")
        # I had to reduce the size to 10.000 pixels to let it work.
        img = pyvips.Image.thumbnail(f, treshold, height=treshold, size="both")
    else:
        # load image in pyvips
        img = pyvips.Image.new_from_file(f, access="sequential")

    # webp conversion
    webpname = f.replace(".jpg", ".webp")
    img.write_to_file(webpname, Q=quality)


# Converting images using multiprocessing

if __name__ == "__main__":
    number_directories = len(os.listdir(working_dir))
    processed = 0
    for d in os.listdir(working_dir):
        print(f"Converting images in {d} directory...")
        current_directory = os.path.join(working_dir, d, "images")
        files = glob(current_directory + "/*.jpg")
        files_to_be_converted = []
        for file in files:
            if file.endswith(".jpg"):
                if os.path.isfile(file.replace(".jpg", ".webp")) is False:
                    files_to_be_converted.append(file)

        start_time = datetime.datetime.now()
        with Pool(10) as pool:
            pool.map(conversion_file, files_to_be_converted)

        # remove previous JPEG images
        for f in files:
            os.remove(f)

        end_time = datetime.datetime.now()
        diff = end_time - start_time
        print(f"Time taken: {diff.seconds} s")
        processed += 1
        print(f"Process completed: {100*float(processed)/number_directories}%")
