# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 11:54:03 2021


Functions for generating input training data, building model layers, training & saving the model

- Includes callbacks for training checkpoints & tensorboard
- Trained model is saved as .h5


@author: Grant Francis
email: gfrancis@uvic.ca

Model architecture inspired and modified from Keras computer vision example:
    https://keras.io/examples/vision/oxford_pets_image_segmentation/
"""

import os
from IPython.display import Image, display
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.optimizers import Adam
import PIL
from PIL import ImageOps
from tensorflow import keras
import numpy as np
from tensorflow.keras import layers
import random





class generator(keras.utils.Sequence):
    """Helper to iterate over the data (as Numpy arrays)."""

    def __init__(self, batch_size, img_size, input_img_paths, target_img_paths):
        self.batch_size = batch_size
        self.img_size = img_size
        self.input_img_paths = input_img_paths
        self.target_img_paths = target_img_paths

    def __len__(self):
        return len(self.target_img_paths) // self.batch_size

    def __getitem__(self, idx):
        """Returns tuple (input, target) correspond to batch #idx."""
        i = idx * self.batch_size
        batch_input_img_paths = self.input_img_paths[i : i + self.batch_size]
        batch_target_img_paths = self.target_img_paths[i : i + self.batch_size]
        x = np.zeros((self.batch_size,) + self.img_size + (3,), dtype="uint8")
        for j, path in enumerate(batch_input_img_paths):
            img = load_img(path, target_size=self.img_size)
            x[j] = img
        y = np.zeros((self.batch_size,) + self.img_size + (1,), dtype="uint8")
        for j, path in enumerate(batch_target_img_paths):
            img = load_img(path, target_size=self.img_size, color_mode="grayscale")
            y[j] = np.expand_dims(img, 2)
            # Ground truth labels are 1, 2, 3. Subtract one to make them 0, 1, 2:
            # y[j] += 1
        return x, y
    
    


def get_model(img_size, num_classes):
    inputs = keras.Input(shape=img_size + (3,))

    ### [First half of the network: downsampling inputs] ###

    # Entry block
    x = layers.Conv2D(32, 3, strides=2, padding="same")(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)

    previous_block_activation = x  # Set aside residual

    # Blocks 1, 2, 3 are identical apart from the feature depth.
    for filters in [64, 128, 256]:
        x = layers.Activation("relu")(x)
        x = layers.SeparableConv2D(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.Activation("relu")(x)
        x = layers.SeparableConv2D(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.MaxPooling2D(3, strides=2, padding="same")(x)

        # Project residual
        residual = layers.Conv2D(filters, 1, strides=2, padding="same")(
            previous_block_activation
        )
        x = layers.add([x, residual])  # Add back residual
        previous_block_activation = x  # Set aside next residual

    ### [Second half of the network: upsampling inputs] ###

    for filters in [256, 128, 64, 32]:
        x = layers.Activation("relu")(x)
        x = layers.Conv2DTranspose(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.Activation("relu")(x)
        x = layers.Conv2DTranspose(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.UpSampling2D(2)(x)

        # Project residual
        residual = layers.UpSampling2D(2)(previous_block_activation)
        residual = layers.Conv2D(filters, 1, padding="same")(residual)
        x = layers.add([x, residual])  # Add back residual
        previous_block_activation = x  # Set aside next residual

    # Add a per-pixel classification layer
    outputs = layers.Conv2D(num_classes, 3, activation="softmax", padding="same")(x)

    # Define the model
    model = keras.Model(inputs, outputs)
    return model





def get_smarter(lib_dir, name, callback_dir, save_dir, c, b, e):
    
    
    pics_dir = lib_dir + '\\pics'
    masks_dir = lib_dir + '\\masks'
    
    num_classes = c
    batch_size = b
    epochs = e

    input_img_paths = sorted(
        [
            os.path.join(pics_dir, fname)
            for fname in os.listdir(pics_dir)
            if fname.endswith(".jpg")
        ]
    )
    target_img_paths = sorted(
        [
            os.path.join(masks_dir, fname)
            for fname in os.listdir(masks_dir)
            if fname.endswith(".png") and not fname.startswith(".")
        ]
    )
    
    
    
    n = len(input_img_paths)
    print('\nNumber of training tile-mask pairs: %s'%n)
    
    
    for input_path, target_path in zip(input_img_paths[:5], target_img_paths[:5]):
        print(input_path, "|", target_path)
    print('...')
    for input_path, target_path in zip(input_img_paths[-5:], target_img_paths[-5:]):
        print(input_path, "|", target_path)
    
    
    
    # Free up RAM in case the model definition cells were run multiple times
    keras.backend.clear_session()
    
    img_size = (160, 160) ### Don't change this. This is the RESIZE for model input
    # Build model
    model = get_model(img_size, num_classes)
    model.summary()
    
    
    
    # Split our img paths into a training and a validation set
    val_samples = np.int(n*0.2) ### 80-20 split
    random.Random(n).shuffle(input_img_paths)
    random.Random(n).shuffle(target_img_paths)
    train_input_img_paths = input_img_paths[:-val_samples]
    train_target_img_paths = target_img_paths[:-val_samples]
    val_input_img_paths = input_img_paths[-val_samples:]
    val_target_img_paths = target_img_paths[-val_samples:]
    
    
    # Instantiate data Sequences for each split
    train_gen = generator(batch_size, img_size, train_input_img_paths, train_target_img_paths)
    val_gen = generator(batch_size, img_size, val_input_img_paths, val_target_img_paths)
    
    
    
    # Configure the model for training.
    # We use the "sparse" version of categorical_crossentropy
    # because our target data is integers.
    model.compile(optimizer='rmsprop', loss="sparse_categorical_crossentropy")
    
    
    
    tensorboard_callback = keras.callbacks.TensorBoard(log_dir=callback_dir, histogram_freq=1)
    checkpoints = keras.callbacks.ModelCheckpoint('%s_chpt.h5'%name, save_best_only=True)
    callbacks = [checkpoints, tensorboard_callback]
    
    
    print('\n\nStarting Training. Library size: %s tile-mask pairs\n...\n\n'%n)
    # Train the model, doing validation at the end of each epoch.
    model.fit(train_gen, epochs=epochs, validation_data=val_gen, callbacks=callbacks, verbose=2)
    
    
    
    model.save(save_dir + '\\%s.h5'%name)
    print('\nTraining complete. Model saved.\n\n')
    
    return











