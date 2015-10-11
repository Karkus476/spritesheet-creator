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

import argparse, os, traceback
from PIL import Image

class Writer:
	def __init__(self, path):
		self.stdx = open(path, 'w')
		self.indentation = 0

	def begin_dir(self, name):
		self.stdx.write("\t"*self.indentation + name + " {\n")
		self.indentation += 1
	
	def add_file(self, name, coords):
		self.stdx.write("\t"*self.indentation + name + ":" + str(coords)+"\n")

	def end_dir(self):
		self.indentation -= 1
		self.stdx.write("\t"*self.indentation + "}\n")
		
	def finish(self):
		self.stdx.close()

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
		writer.add_file(self.filename, self.get_loc())
	
	def get_loc(self):
		return self.x, self.y

	def set_loc(self, loc):
		self.x = loc[0]
		self.y = loc[1]
		
	def get(self, result):
		'''
		For use in recursive Directory.get()
		'''
		result.append(self.image)
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
				print("Directory:", full_path)
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

def all_fit(images, enclosing=None):
	'''
	See:
	http://www.codeproject.com/Articles/210979/Fast-optimizing-rectangle-packing-algorithm-for-bu
	to try to understand this function.
	@param images: Set of images to fit into enclosing
	@param enclosing: rectangle (width, height)
	'''
	#Enclosing rectangle. -1 means no limit
	# [-1, height of first (largest) image]
	if not enclosing:
		enclosing = (-1, images[0].size[1])
	
	#A 2D array of booleans.
	occupied = [[False]]
	column_widths = [enclosing[0]]
	row_heights = [enclosing[1]]
	
	#Array of images
	final_images = []
	
	#For each image,
	for rect in (image.size for image in images):
		#Check all rows,
		for row, height in zip(occupied, row_heights):
			#and cells in those rows,
			for cell, width in zip(row, column_widths):
				#to see if the image fits
				if cell:
					if rect[0] <= width and rect[1] <= height:
						column_widths.append(width - rect[0])
						row_heights.append(height - rect[1])
				else:
					pass
					
	
def organise(images, enclosing):
	'''
	@param images: Ordered in height order, tallest first
	@return: (final image size, list of lists: [path, (x, y), Image])
	'''
	final_size = 0
	final_images = []
	for image in images:
		final_size += image.size[0]
		final_images.append((image, (final_size, 0)))
	return (final_size, images[0].size[1]), final_images

def start():
	#Parse all arguments as string paths to image files
	parser = argparse.ArgumentParser()
	parser.add_argument("base", help="Parent directory of images to add to spritesheet",type=str)
	parser.add_argument("output", help="Output file path.",type=str)
	parser.add_argument("index", help="Output .stdx path.",type=str)
	args = parser.parse_args()
	print("Loading all images from:", args.base)
	
	base_dir = Directory(args.base)
	images = base_dir.get([])

	#Sort images by height, largest first.
	images = sorted(images, key=lambda val: val.size[1])
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
	for image, loc in organisation[1]:
		final.paste(image, loc)
	print("Saving as", args.output + "...")
	final.save(args.output)
	
	print("Writing Index File...")
	writer = Writer(args.index)
	base_dir.write(writer)
	writer.finish()

if __name__ == "__main__":
	start()
