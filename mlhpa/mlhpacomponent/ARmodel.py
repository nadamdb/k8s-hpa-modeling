import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.ar_model import AR 
import tensorflow as tf


class myAR(object):
    def __init__(self):
        self.model = None
        self.scaler_load = None
        self.scaler_diff = None
        self.df = None
        self.batch_size = 32

        self.in_forecast = False
        self.in_training = False
        self.in_change = False

    def train(self, tsData, nb_epochs = 40, batchSize = 32):
        """
        Trains the LSTM on the initial TimeSeries data. 
        
        tsData can be pandas object with DateTimeIndex or a numpy array
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
        
        # Scale the input train data
        temp_scaler_load = StandardScaler()
        temp_df['scaledLoad'] = temp_scaler_load.fit_transform(temp_df[['load']])
        
        # Reshape the input to the desired form
        # df_train = self.df[['scaledLoad', 'scaledDiff', 'outVal']].dropna().values
        
        # Create AR Network
        temp_model = AR(temp_df.scaledLoad).fit()
        while self.in_forecast:
            print('Training is waiting for forecast finish to change the model')
        self.in_change = True
        self.model = temp_model
        self.scaler_load = temp_scaler_load
        self.df = temp_df
        self.in_change = False

    def addTsValue(self, newTsVal):
        """
        Append new values to the existing load history
        """
        newDf = newTsVal
        if not hasattr(type(newDf), '__iter__'): 
            newDf = np.array([newDf])
        else:
            newDf = np.array(newDf)

        newDf = pd.DataFrame({'load': newDf})
        
        # newDf['diff'] = newDf.load.diff()
        # newDf['outVal'] = newDf.load.shift(-1)
        
        # newDf['scaledDiff'] = self.scaler_diff.transform(newDf[['diff']])
        newDf['scaledLoad'] = self.scaler_load.transform(newDf[['load']])
        # newDf['outVal'] = self.scaler_load.transform(newDf[['outVal']])
        
        # newDf = newDf.iloc[1:]
        
        self.df = pd.concat([self.df, newDf], sort=False).reset_index(drop=True)
        return newDf
    
    def makeTestPrediction(self, inputData):
        """
        Evaluates all input test data, and returns them
        """
        
        # add input data to dataframe:
        df_test = self.addTsValue(inputData)
        
        window = self.model.k_ar
        coef = self.model.params
        
        history = list(df_test.scaledLoad.values[-window:])
        predictions = list()
        
        for t in range(df_test.shape[0]):
            length = len(history)
            lag = [history[i] for i in range(length - window, length)]
            yhat = coef[0]
            for d in range(window):
                yhat += coef[d+1] * lag[ window - d - 1 ]
            obs = df_test.scaledLoad.values[t]
            
            predictions.append(float(yhat))
            history.append(float(obs))
        
        return df_test

    # make a one-step forecast
    def forecast(self):
        """
        Makes a prediction based on the last element of the inner history of the model.
        """
        while self.in_change:
            print('Forecast is waiting for model change')
        self.in_training = True
        window = self.model.k_ar
        coef = self.model.params
        
        history = list(self.df.scaledLoad.values[-window:])        
        length = len(history)
        
        lag = [history[i] for i in range(length - window, length)]
        yhat = coef[0]
        for d in range(window):
            yhat += coef[d+1] * lag[window-d-1]

        self.in_training = False
        return self.scaler_load.inverse_transform(np.array([float(yhat)]))[0]
