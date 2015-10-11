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


from PIL import Image

class Rect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def intersects(self, rect):
        return (self.x > rect.x - self.width and self.x < rect.x + rect.width and
            self.y > rect.y - self.height and self.y < rect.y + rect.height)
        
    def to_string(self):
        return ("("+ str(self.x) + ", " + str(self.y) + "), "+
                "("+ str(self.width) + ", " + str(self.height) + ")")

class EnclosingRect:
    def __init__(self):
        self.positions = [(0, 0)]
        self.rects = []
        
    def add_rect(self, width, height):
        rect = Rect(0, 0, width, height)
        #Positions where it doesn't intersect any other images
        viable = []
        for pos in self.positions:
            rect.x = pos[0]
            rect.y = pos[1]
            if self.intersects_any(rect):
                continue
            viable.append(Rect(pos[0], pos[1], width, height))
            
        best = min(viable, key=self.how_good_with)
        self.positions.remove((best.x, best.y))
        self.positions.append((best.x + width, best.y))
        self.positions.append((best.x, best.y + height))
        self.rects.append(best)
        return (best.x, best.y)
    
    def how_good_with(self, new):
        w, h = self.get_size(self.rects + [new])
        return w*h
    
    def get_area(self, rects):
        w, h = self.get_size(rects)
        return w * h
    
    def get_size(self, rects):
        '''
        @return: total width, height of enclosing rect
        '''
        x_max = max(rects, key=lambda rect: rect.x + rect.width)
        y_max = max(rects, key=lambda rect: rect.y + rect.height)
        return (x_max.x + x_max.width) , (y_max.y + y_max.height)
                    
    def intersects_any(self, rect):
        for r in self.rects:
            if rect.intersects(r):
                return True
        return False
        