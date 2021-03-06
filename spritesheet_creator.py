# A Script to generate a spritesheet and .stdx file
# recursively from files in an input directory
# Usage: 
# python3 spritesheet_creator.py [-h] <input dir> <output image> <output text>
# Copyright (C) 2015 Karkus476 <karkus476@yahoo.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse, os, traceback, datetime
from PIL import Image
from packing import EnclosingRect
from sexpr_writer import SExprWriter

class Writer(SExprWriter):
	def __init__(self, path):
		super().__init__(open(path, 'w'))
		self.write_comment("Generated by Sprite Sheet Creator")
		self.write_comment("It is recommended you do not edit this file.")

	def begin_dir(self, name):
		self.begin_list("directory")
		self.write("name", name)
	
	def add_file(self, name, coords, size):
		self.begin_list("file")
		self.write("name", name)
		self.write_int("x", coords[0])
		self.write_int("y", coords[1])
		self.write_int("width", size[0])
		self.write_int("height", size[1])
		self.end_list()
        
	def end_dir(self):
		self.end_list()
		
	def finish(self):
		self.fout.close()

class ImageFile:
	@staticmethod
	def from_path(filename, path):
		try:
			image = Image.open(path)
		except IOError:
			image = None
		if image:
			return ImageFile(filename, image)
		else:
			return None

	def __init__(self, filename, image):
		self.filename = filename
		self.image = image
		
		self.x = 0
		self.y = 0
	
	def write(self, writer):
		writer.add_file(self.filename, self.get_loc(), self.image.size)
	
	def get_loc(self):
		return self.x, self.y

	def set_loc(self, loc):
		self.x = loc[0]
		self.y = loc[1]
		
	def get(self, result):
		'''
		For use in recursive Directory.get()
		'''
		result.append(self)
		return result

class Directory:

	def __init__(self, path, dirname=None):
		self.children = []
		self.name = dirname
		for name in os.listdir(path):
			full_path = os.path.join(path, name)
			if os.path.isfile(full_path):
				image_file = ImageFile.from_path(name, full_path)
				if image_file:
					self.children.append(image_file)
				else:
					pass #file not image
			elif os.path.isdir(full_path):
				directory = Directory(full_path, name)
				self.children.append(directory)
			else:
				print("Unexpected object in "+
				      "path: "+full_path+" is "+
				      "neither file nor directory.")
	
	def write(self, writer):
		#If name is None, then this is top dir so don't make new tag in file.
		if self.name:
			writer.begin_dir(self.name)
		#Recursively write to file. Whether child is dir or file doesn't matter
		# as both have .write() attributes
		for child in self.children:
			child.write(writer)
		if self.name:
			writer.end_dir()
			
	def get(self, result):
		'''
		Recursively fetch all image files in this directory
		'''
		for child in self.children:
			result = child.get(result)
		return result
					
	
def organise(images):
	'''
	@param images: Ordered in height order, tallest first
	@return: (final image size, list of lists: [(Image, loc)])
	'''
	enclosing = EnclosingRect()
	one_percent = round(len(images) / 100)
	counter = 0
	print("Packing Images Onto Spritesheet")
	before = datetime.datetime.now()
	for imgfile in images:
		imgfile.set_loc(enclosing.add_rect(imgfile.image.size[0], imgfile.image.size[1]))
		counter += 1
		if one_percent and counter % one_percent == 0:
			print(str(int(counter/one_percent)) + "%")
	print("Done. Took", str((datetime.datetime.now() - before).seconds) +"s")
	return enclosing.get_size(enclosing.rects), images

def start():
	#Parse all arguments as string paths to image files
	parser = argparse.ArgumentParser()
	parser.add_argument("output", help="Output file path.",type=str)
	parser.add_argument("images", help="Images to add to spritesheet",type=str, nargs="*")
	args = parser.parse_args()
	print("Loading all images from:", args.base)
	
	base_dir = Directory(args.base)
	images = base_dir.get([])
	print("Found", len(images), "images.")

	#Sort images by height, largest first.
	images = sorted(images, key=lambda img: img.image.size[1])
	images = list(reversed(images))
	#Debug: Print images and heights
	#for img in images:
	#	print("Path:", img[0], "Height:", img[1].size[1])
	
	#Get x, y values
	organisation = organise(images)

	#Debug: Print images, locations and heights
	#for path, loc, height in organisation[1]:
	#	print("Path:", path, "Loc:", loc,"Height:", height)

	print("Planned Size:", organisation[0])
	#Create Image to hold sprites
	final = Image.new("RGBA", organisation[0], (0,0,0,0))
	print("Pasting files onto blank image...")
	for image in organisation[1]:
		final.paste(image.image, image.get_loc())
	print("Saving as", args.output + "...")
	final.save(args.output)
	
	print("Writing Index File...")
	writer = Writer(args.index)
	base_dir.write(writer)
	writer.finish()

if __name__ == "__main__":
	start()
