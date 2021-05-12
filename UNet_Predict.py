# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 14:40:06 2021


Functions to deploy model on imput image tiles & re-pair each prediction with each input tile


@author: Grant Francis
email: gfrancis@uvic.ca
"""

import os
from tensorflow.keras.preprocessing.image import load_img
import PIL
from PIL import ImageOps, Image
from tensorflow import keras
import numpy as np
from tensorflow.keras.preprocessing.image import load_img




def get_name(file_location):
    filename = file_location.split('\\')[-1]
    filename = filename.split('.')

    return int(filename[0])



def deploy_model(saved_model, pics_dir, save_dir):


    num_classes = 2
    batch_size = 1


    input_img_paths = sorted([
            os.path.join(pics_dir, fname)
            for fname in os.listdir(pics_dir)
            if fname.endswith(".jpg")
        ])



    n = len(input_img_paths)
    print('\n\nMaking predictions for %s tiles...\n'%n)



    class generator(keras.utils.Sequence):
        """Helper to iterate over the data (as Numpy arrays)."""

        def __init__(self, batch_size, img_size, input_img_paths):
            self.batch_size = batch_size
            self.img_size = img_size
            self.input_img_paths = input_img_paths

        def __len__(self):
            return len(self.input_img_paths) // self.batch_size

        def __getitem__(self, idx):
            """Returns tuple (input, target) correspond to batch #idx."""
            i = idx * self.batch_size
            batch_input_img_paths = self.input_img_paths[i : i + self.batch_size]
            x = np.zeros((self.batch_size,) + self.img_size + (3,), dtype="uint8")
            for j, path in enumerate(batch_input_img_paths):
                img = load_img(path, target_size=self.img_size)
                x[j] = img

            return x


    # Free up RAM in case the model definition cells were run multiple times
    keras.backend.clear_session()


    model = keras.models.load_model(saved_model)
    # model.summary()

    img_size = (160, 160) ### Don't change this. This is the RESIZE for model input
    img_gen = generator(batch_size, img_size, input_img_paths)
    preds = model.predict(img_gen)


    print('\nSaving predictions...')
    ### Save predictions
    for i in range(preds[:,0,0,0].size):
        mask = np.argmax(preds[i], axis=-1)
        mask = np.expand_dims(mask, axis=-1)
        img = PIL.ImageOps.autocontrast(keras.preprocessing.image.array_to_img(mask))
        name = get_name(input_img_paths[i])
        saved_mask_png = save_dir + '\\%s.png'%name
        arr = np.array(img)
        Image.fromarray(arr.astype(np.uint8)).save(saved_mask_png)

    print('Saved %s prediction tiles.    Dimensions: %s\n'%(preds[:,0,0,0].size, str(preds.shape)))

    return
