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

working_dir = os.path.join("tmp", "images")


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


def conversion_file(f, quality=10):
    img = pyvips.Image.new_from_file(f, access="sequential")
    webpname = f.replace(".jpg", ".webp")
    img.write_to_file(webpname, Q=quality)


# Converting images using multiprocessing

if __name__ == "__main__":
    for d in os.listdir(working_dir):
        print(f"Converting images in {d} directory...")
        start_time = datetime.datetime.now()
        current_directory = os.path.join(working_dir, d, "images")
        # print(f"Current directory path: {current_directory}")
        files = glob(current_directory + "/*.jpg")
        # print(f"list of files: {files}")
        with Pool(12) as pool:
            pool.map(conversion_file, files)

        # remove previous JPEG images
        for f in files:
            os.remove(f)

        end_time = datetime.datetime.now()
        diff = end_time - start_time
        print(f"Time taken: {diff.seconds} s")
