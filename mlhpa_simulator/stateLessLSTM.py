import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import keras
from keras.models import Sequential  
from keras.layers import Dense  
from keras.layers import LSTM  
from keras.layers import Dropout  
import tensorflow as tf


class myLSTM(object):

    def __init__(self):
        self.model = None
        self.scaler_load = None
        self.scaler_diff = None
        # df is the history
        self.df = None
        self.n_steps = 15
        self.n_features = 2
        self.batch_size = 32

        self.in_forecast = False
        self.in_training = False
        self.in_change = False

    # split a multivariate sequence into samples
    def split_sequences(self, sequences, n_steps):
        X, y = list(), list()
        for i in range(len(sequences)):
            # find the end of this pattern
            end_ix = i + n_steps
            # check if we are beyond the dataset
            if end_ix > len(sequences):
                break
            # gather input and output parts of the pattern
            seq_x, seq_y = sequences[i:end_ix, : -1], sequences[end_ix - 1, -1]
            X.append(seq_x)
            y.append(seq_y)
        return np.array(X), np.array(y)
    
    def train(self, tsData, nb_epochs=40, batchSize=32):
        """
        Trains the LSTM on the initial TimeSeries data. 
        
        tsData can be pandas object with DateTimeIndex or a numpy array
        tsData: list with numbers or pandas series
        nb_epochs: 20 maybe better
        batchSize: 32 ok
        """
        self.in_training = True
        if self.batch_size != batchSize:
            self.batch_size = batchSize
        
        # if self.model is not None:
        #     print('Model is already trained')
        #     return
        
        # TODO input validation
        temp_df = pd.DataFrame(tsData).copy()
        temp_df.columns = ['load']
        
        temp_df['diff'] = temp_df.load.diff()
        temp_df['outVal'] = temp_df.load.shift(-1)
        
        # Scale the input train data
        temp_scaler_load = StandardScaler()
        temp_df['scaledLoad'] = temp_scaler_load.fit_transform(temp_df[['load']])
        temp_df['outVal'] = temp_scaler_load.transform(temp_df[['outVal']])
        
        temp_scaler_diff = StandardScaler()
        temp_df['scaledDiff'] = temp_scaler_diff.fit_transform(temp_df[['diff']])
        
        # Reshape the input to the desired form
        df_train = temp_df[['scaledLoad', 'scaledDiff', 'outVal']].dropna().values
        X, y = self.split_sequences(df_train, self.n_steps)

        # Create LSTM Network
        temp_model = Sequential()

        temp_model.add(LSTM(units=50, activation='relu', return_sequences=True,
                       input_shape=(self.n_steps, self.n_features)))
        temp_model.add(Dropout(0.2))

        temp_model.add(LSTM(units=50, activation='relu', return_sequences=True))
        temp_model.add(Dropout(0.2))

        temp_model.add(LSTM(units=50, activation='relu', return_sequences=True))
        temp_model.add(Dropout(0.2))

        temp_model.add(LSTM(units=50, activation='relu'))
        temp_model.add(Dropout(0.2))

        temp_model.add(Dense(units=1))
        
        temp_model.compile(optimizer='adam', loss='mean_squared_error')
        
        temp_model.fit(X, y, epochs=nb_epochs, batch_size=self.batch_size, verbose=2)
        temp_model._make_predict_function()
        while self.in_forecast:
            print('Training is waiting for forecast finish to change the model')
        self.in_change = True
        self.model = temp_model
        self.df = temp_df
        self.scaler_diff = temp_scaler_diff
        self.scaler_load = temp_scaler_load
        self.in_change = False
        self.in_training = False
        '''
        for i in range(nb_epochs):
            model.fit(X, y, epochs = 1, batch_size = batch_size, verbose=2, shuffle=False) 
            model.reset_states()
        '''
    
    def addTsValue(self, newTsVal):
        """
        Append new values to the existing load history
        newTsVal: number or list of numbers
        """
        if self.in_change:
            return
        newDf = newTsVal
        if not hasattr(type(newDf), '__iter__'):
            newDf = np.array([newDf])
        else:
            newDf = np.array(newDf)
        
        # Update the previous ones
        self.df.iloc[-1, self.df.columns.get_loc('outVal')] = newDf[0]
        # The first line equals with the previous last line
        newDf = np.insert(newDf, 0, self.df.iloc[-1].load )
        newDf = pd.DataFrame({'load': newDf})
        
        newDf['diff'] = newDf.load.diff()
        newDf['outVal'] = newDf.load.shift(-1) 
        
        newDf['scaledDiff'] = self.scaler_diff.transform(newDf[['diff']])
        newDf['scaledLoad'] = self.scaler_load.transform(newDf[['load']])
        newDf['outVal'] = self.scaler_load.transform(newDf[['outVal']])
        
        newDf = newDf.iloc[1:]
        
        self.df = pd.concat([self.df, newDf], sort=False).reset_index(drop=True)
        return newDf
    
    def makeTestPrediction(self, inputData):
        """
        Evaluates all input test data, and returns them
        inputData:
        """
        # add input data to dataframe:
        df_test = self.addTsValue(inputData)
        print(df_test.shape)
        df_test_with_prevtrain = self.df.iloc[- (self.n_steps + df_test.shape[0] - 1) :]
        print(df_test_with_prevtrain.shape)
        
        X_input = df_test_with_prevtrain[['scaledLoad', 'scaledDiff', 'outVal']].values
        print(X_input.shape)
        # convert into input/output
        X_test, y_test = self.split_sequences(X_input, self.n_steps)
        print(X_test.shape)
        
        # predict
        preds = self.model.predict(X_test)
        # Store the predictions in the test dataFrame
        df_test['preds'] = preds[:, 0]
        return df_test

    # make a one-step forecast
    def forecast(self):
        """
        Makes a prediction based on the last element of the inner history of the model.
        """
        while self.in_change:
            print('Forecast is waiting for model change')
        self.in_forecast = True
        # add input data to dataframe:
        df_test_with_prevtrain = self.df.iloc[-self.n_steps:]
        
        X_input = df_test_with_prevtrain[['scaledLoad', 'scaledDiff', 'outVal']].values
        # convert into input/output
        X_test, y_test = self.split_sequences(X_input, self.n_steps)
        
        # predict
        preds = self.model.predict(X_test)
        preds = self.scaler_load.inverse_transform(preds)
        # Store the predictions in the test dataFrame
        self.in_forecast = False
        return preds[0][0]
