# pip install --upgrade pip
# pip install requests
# pip --no-cache-dir install --upgrade https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow_gpu-1.9.0-cp36-cp36m-linux_x86_64.whl
# pip install keras
# git clone https://www.github.com/dmarx/SuicideWatch.git

import time
import sqlite3
from contextlib import closing

import requests
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

from keras.datasets import imdb
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence

np.random.seed(123)

db_path = '/home/SuicideWatch/data/scrape_results.db'

with closing(sqlite3.connect(db_path)) as conn:
    text_lens = conn.execute('select length(text) from sentences').fetchall()

sns.distplot(np.log(text_lens))
plt.show()

np.quantile(text_lens, np.arange(10)/10)
# array([  3.,  23.,  31.,  40.,  50.,  61.,  74.,  89., 110., 146.])

np.quantile(text_lens, .9+np.arange(10)/100)
# array([146., 151., 157., 165., 173., 183., 196., 213., 239., 291.])

np.quantile(text_lens, .99 + np.arange(10)/1000)
# array([291., 300., 310., 323., 338., 357., 384., 422., 490., 640.])

# Sentence length is lognormally distributed.
# 99.8% of sentences are 490 chars or shorter. Let's pad to 500.


# fuck it, let's just prototype this with some test sentences
test_sentences = (
    "This is the song that never ends.",
    "Yes it goes on and on my friends!",
    "Some people, started, singing it, not knowing what it was, but they continued singing it forever just because..."
)

# via https://stanford.edu/~shervine/blog/keras-how-to-generate-data-on-the-fly.html
class DataGenerator(keras.utils.Sequence):
    'Generates data for Keras'
    def __init__(self, list_IDs, labels, batch_size=32, dim=(32,32,32), n_channels=1,
                 n_classes=10, shuffle=True):
        'Initialization'
        self.dim = dim
        self.batch_size = batch_size
        self.labels = labels
        self.list_IDs = list_IDs
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.shuffle = shuffle
        self.on_epoch_end()

    def __len__(self):
        'Denotes the number of batches per epoch'
        return int(np.floor(len(self.list_IDs) / self.batch_size))

    def __getitem__(self, index):
        'Generate one batch of data'
        # Generate indexes of the batch
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]

        # Find list of IDs
        list_IDs_temp = [self.list_IDs[k] for k in indexes]

        # Generate data
        X, y = self.__data_generation(list_IDs_temp)

        return X, y

    def on_epoch_end(self):
        'Updates indexes after each epoch'
        self.indexes = np.arange(len(self.list_IDs))
        if self.shuffle == True:
            np.random.shuffle(self.indexes)

    def __data_generation(self, list_IDs_temp):
        'Generates data containing batch_size samples' # X : (n_samples, *dim, n_channels)
        # Initialization
        X = np.empty((self.batch_size, *self.dim, self.n_channels))
        y = np.empty((self.batch_size), dtype=int)

        # Generate data
        for i, ID in enumerate(list_IDs_temp):
            # Store sample
            X[i,] = np.load('data/' + ID + '.npy')

            # Store class
            y[i] = self.labels[ID]

        return X, keras.utils.to_categorical(y, num_classes=self.n_classes)
