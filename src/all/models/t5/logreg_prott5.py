# libraries
import pandas as pd 
import numpy as np 
from sklearn import preprocessing
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import pickle
from sklearn.metrics import confusion_matrix, accuracy_score, f1_score, classification_report, matthews_corrcoef, balanced_accuracy_score

# load files
# dataset import
# train 
ds_train = pd.read_csv('Y_Train_SF.csv')
y_train = list(ds_train["SF"])

filename = 'SF_Train_ProtT5.npz'
X_train = np.load(filename)['arr_0']
filename = 'Other_Train_US.npz'
X_train_other = np.load(filename)['arr_0']

X_train = np.concatenate((X_train, X_train_other), axis=0)

for i in range(len(X_train_other)):
    y_train.append('other')

# val
ds_val = pd.read_csv('Y_Val_SF.csv')
y_val = list(ds_val["SF"])

filename = 'SF_Val_ProtT5.npz'
X_val = np.load(filename)['arr_0']

filename = 'Other_Val_US.npz'
X_val_other = np.load(filename)['arr_0']

X_val = np.concatenate((X_val, X_val_other), axis=0)

for i in range(len(X_val_other)):
    y_val.append('other')

# test
ds_test = pd.read_csv('Y_Test_SF.csv')
y_test = list(ds_test["SF"])

filename = 'SF_Test_ProtT5.npz'
X_test = np.load(filename)['arr_0']

filename = 'Other_Test_US.npz'
X_test_other = np.load(filename)['arr_0']

X_test = np.concatenate((X_test, X_test_other), axis=0)

for i in range(len(X_test_other)):
    y_test.append('other')

# y process
y_tot = []

for i in range(len(y_train)):
    y_tot.append(y_train[i])

for i in range(len(y_val)):
    y_tot.append(y_val[i])

for i in range(len(y_test)):
    y_tot.append(y_test[i])

le = preprocessing.LabelEncoder()
le.fit(y_tot)

y_train = np.asarray(le.transform(y_train))
y_val = np.asarray(le.transform(y_val))
y_test = np.asarray(le.transform(y_test))

num_classes = len(np.unique(y_tot))
print(num_classes)
print("Loaded X and y")

# logistic regression
print("Training\n")
clf = LogisticRegression(random_state=0, verbose=1, max_iter = 10).fit(X_train, y_train)

print("Testing\n")
y_pred_test = clf.predict(X_test)
f1_score_test = f1_score(y_test, y_pred_test, average = 'weighted')
acc_score_test = accuracy_score(y_test, y_pred_test)
mcc_score = matthews_corrcoef(y_test, y_pred_test)
bal_acc = balanced_accuracy_score(y_test, y_pred_test)

print("F1 Score: ", f1_score_test)
print("Acc Score: ", acc_score_test)
print("MCC: ", mcc_score)
print("Bal Acc: ", bal_acc)



'''
Test Accuracy:
Accuracy:  0.8311530166132323 0.004434521005535827
F1-Score:  0.6696653667318053 0.007206807131046288
MCC:  0.8303846024636431 0.0044521941066568765
Bal Acc:  0.7030649478628275 0.006701573646370803
'''