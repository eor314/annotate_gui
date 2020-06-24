"""
 Main script for sorting images in a folder into subfolders. This script launches a GUI which displays
 one image after the other and lets the user vote for different given labels from a list given as input to the
 script.
 USAGE:
 python sort_folder.py --folder <INPUT-FOLDER> --labels <INPUT-LABEL1> <INPUT-LABEL2> ...
 Author: Christian Baumgartner (c.baumgartner@imperial.ac.uk)
 Date: 31. Jan 2016

 Version 2.0
 Author: Eric Orenstein
 Date: Mar 24 2020
"""

import argparse
import tkinter as tk
import os
from shutil import copyfile, move
from PIL import ImageTk, Image, ImageOps

class ImageGui:
    """
    GUI for iFind1 image sorting. This draws the GUI and handles all the events.
    Useful, for sorting views into sub views or for removing outliers from the data.
    """

    def __init__(self, master, labels, paths, out_dict=False, out_file=False):
        """
        Initialise GUI
        :param master: The parent window
        :param labels: A list of labels that are associated with the images
        :param paths: A list of file paths to images
        :param out_dict: A switch between copying images and saving a text
        :param out_file: where to save image lists
        :return:
        """

        # So we can quit the window from within the functions
        self.master = master

        # Extract the frame so we can draw stuff on it
        frame = tk.Frame(master)

        # Initialise grid
        frame.grid()

        # Start at the first file name
        self.index = 0
        self.paths = paths
        self.labels = labels
        self.out_dict = out_dict
        self.out_file = out_file

        # Number of labels and paths
        self.n_labels = len(labels)
        self.n_paths = len(paths)

        # Set empty image container
        self.image_raw = None
        self.image = None
        self.image_panel = tk.Label(frame)

        # set image container to first image or stopping point
        # check if an out_file is defined
        if self.out_file:
            # if it is see if there are already annotations in the desired files
            if os.path.exists(os.path.join(self.out_file, self.labels[0]+'.txt')):
                self.index = self._restart_from_file(self.labels, self.out_file)

        self.set_image(paths[self.index])

        # Make buttons
        self.buttons = []
        for label in labels:
            self.buttons.append(
                    tk.Button(frame, text=label, width=10, height=1, command=lambda l=label: self.vote(l))
            )

        # Add progress label
        progress_string = "%d/%d" % (self.index, self.n_paths)
        self.progress_label = tk.Label(frame, text=progress_string, width=10)

        # Place buttons in grid
        for ll, button in enumerate(self.buttons):
            button.grid(row=0, column=ll, sticky='we')
            #frame.grid_columnconfigure(ll, weight=1)

        # Place progress label in grid
        self.progress_label.grid(row=0, column=self.n_labels, sticky='we')

        # Place the image in grid
        self.image_panel.grid(row=1, column=0, columnspan=self.n_labels+1, sticky='we')

        # add a save button at bottom
        self.save_button = tk.Button(frame, text='save', width=10, height=1, command=lambda: self.save())
        self.save_button.grid(row=3, column=0, columnspan=2, stick='we')

        # key bindings (so number pad can be used as shortcut)
        for key in range(self.n_labels):
            master.bind(str(key+1), self.vote_key)

    def show_next_image(self):
        """
        Displays the next image in the paths list and updates the progress display
        """
        self.index += 1
        progress_string = "%d/%d" % (self.index, self.n_paths)
        self.progress_label.configure(text=progress_string)

        if self.index < self.n_paths:
            self.set_image(self.paths[self.index])
        else:
            # save the labels at the end
            if self.out_file:
                self.save()
            self.master.quit()

    def set_image(self, path):
        """
        Helper function which sets a new image in the image view
        :param path: path to that image
        """
        image = self._load_image(path)
        self.image_raw = image
        self.image = ImageTk.PhotoImage(image)
        self.image_panel.configure(image=self.image)

    def vote(self, label):
        """
        Processes a vote for a label: Initiates the file copying and shows the next image
        :param label: The label that the user voted for
        """
        input_path = self.paths[self.index]
        if self.out_dict:
            self._add_to_dict(self.out_dict, input_path, label)
        else:
            self._copy_image(input_path, label)
        self.show_next_image()

    def vote_key(self, event):
        """
        Processes voting via the number key bindings.
        :param event: The event contains information about which key was pressed
        """
        pressed_key = int(event.char)
        label = self.labels[pressed_key-1]
        self.vote(label)

    def save(self):
        """
        Save the output dictionary
        """
        for kk in self.out_dict.keys():
            temp = os.path.join(self.out_file, kk+'.txt')
            with open(temp, 'w') as fobj:
                for line in self.out_dict[kk]:
                    fobj.write(os.path.basename(line) + '\n')
                fobj.close()
            print('saved', temp)

    @staticmethod
    def _load_image(path, size=(800, 600)):
        """
        Loads and resizes an image from a given path using the Pillow library
        :param path: Path to image
        :param size: Size of display image
        :return: Resized image
        """
        image = Image.open(path)
        ratio = min(size[1] / image.size[1], size[0] / image.size[0])
        width = int(image.size[0] * ratio)
        height = int(image.size[1] * ratio)
        image = image.resize((width, height), Image.BICUBIC)

        delta_w = size[0] - image.size[0]
        delta_h = size[1] - image.size[1]
        pad = (delta_w // 2, delta_h // 2, delta_w - (delta_w // 2), delta_h - (delta_h // 2))
        image = ImageOps.expand(image, pad)
        #image = image.resize(size, Image.ANTIALIAS)
        #image = image.thumbnail(size, Image.ANTIALIAS)
        return image

    @staticmethod
    def _expand_to_square(img, size):
        """
        expands the dimensions of the image to be square
        :param img: PIL image
        :param size: desired size as tuple (width, height)
        :return: padded PIL image
        """
        delta_w = size[0] - img.size[0]
        delta_h = size[1] - img.size[1]
        pad = (delta_w // 2, delta_h // 2, delta_w - (delta_w // 2), delta_h - (delta_h // 2))
        out = ImageOps.expand(img, pad)

        return out

    @staticmethod
    def _copy_image(input_path, label):
        """
        Copies a file to a new label folder using the shutil library. The file will be copied into a
        subdirectory called label in the input folder.
        :param input_path: Path of the original image
        :param label: The label
        """
        root, file_name = os.path.split(input_path)
        output_path = os.path.join(root, label, file_name)
        print(" %s --> %s" % (file_name, label))
        copyfile(input_path, output_path)
        #os.symlink(input_path, output_path)

    @staticmethod
    def _add_to_dict(output_dict, input_path, label):
        """
        Adds a file path to the appropriate field in the output dictrionary
        :param output_dict: dictionary for holding labels
        :param input_path: path of image that was classified
        :param label: the assigned label
        :return:
        """
        output_dict[label].append(input_path)
        print(" %s --> %s" % (os.path.basename(input_path), label))
        #print(output_dict[label])

    @staticmethod
    def _move_image(input_path, label):
        """
        Moves a file to a new label folder using the shutil library. The file will be moved into a
        subdirectory called label in the input folder. This is an alternative to _copy_image, which is not
        yet used, function would need to be replaced above.
        :param input_path: Path of the original image
        :param label: The label
        """
        root, file_name = os.path.split(input_path)
        output_path = os.path.join(root, label, file_name)
        print(" %s --> %s" % (file_name, label))
        move(input_path, output_path)

    @staticmethod
    def _restart_from_file(labs, ptf):
        """
        Checks where in a label effort you are
        :param labels: list of labels
        :param ptf: the path were the output folders are
        :return: index of image to start on
        """

        temp = [os.path.join(ptf, item+'.txt') for item in labels]
        tot = 0
        for lab in temp:
            with open(lab, 'r') as fobj:
                tot += sum(1 for line in fobj)
                fobj.close()
        return tot

def make_folder(directory):
    """
    Make folder if it doesn't already exist
    :param directory: The folder destination path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

# The main bit of the script only gets exectured if it is directly called
if __name__ == "__main__":

    # Make input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--folder', help='Input folder where the *tif images should be', required=True)
    parser.add_argument('-l', '--labels', nargs='+', help='Possible labels in the images', required=True)
    parser.add_argument('-t', '--textfile', help='text file name if sorting classifier output', required=False)
    parser.add_argument('-o', '--output', help='format of output', default='copy', choices=['copy', 'txt'])
    parser.add_argument('-i', '--image_folder', help='if using list of images, path where actual images live', required=False)
    args = parser.parse_args()

    # grab input arguments from args structure
    input_folder = args.folder
    labels = args.labels
    oput = args.output
    txt = args.textfile
    imgfold = args.image_folder

    # Make folder for the new labels
    if oput == 'copy':
        for label in labels:
            make_folder(os.path.join(input_folder, label))

    else:
        # make a dictionary for printing to file later
        outdict = dict()

        # make a new key for each label
        for label in labels:
            outdict[label] = []

    # Put all image file paths into a list
    if not txt:
        paths = []
        for file in os.listdir(input_folder):
            if file.endswith(".jpeg") or file.endswith(".tiff") or file.endswith(".jpg"):

                path = os.path.join(input_folder, file)
                paths.append(path)
    else:
        with open(os.path.join(input_folder, txt), 'r') as ff:
            paths = list(ff)
            ff.close()

        paths = [os.path.join(imgfold, line.strip()) for line in paths]

    # Start the GUI
    root = tk.Tk()
    #root.geometry("1000x1000")
    if outdict:
        app = ImageGui(root, labels, paths, out_dict=outdict, out_file=input_folder)
    else:
        app = ImageGui(root, labels, paths)
    root.mainloop()