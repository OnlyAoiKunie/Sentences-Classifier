# -*- coding: utf-8 -*-
"""HW.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wfqOdfEbuKitW_iSskX2mJJ8zn9YFqq5
"""

!pip install transformers
from transformers import BertTokenizer
from transformers import BertModel
import torch
from torch import nn as nn
from torch.optim import Adam
import numpy as np

tokenizer = BertTokenizer.from_pretrained('bert-base-cased')

testing_data_path = '/content/drive/MyDrive/test/dialogues_test.txt'
training_data_path = '/content/drive/MyDrive/train/dialogues_train.txt'
testing_topic_path = '/content/drive/MyDrive/test/dialogues_test_topic.txt'
training_topic_path = '/content/drive/MyDrive/train/dialogues_train_topic.txt'

class Dataset(torch.utils.data.Dataset): #定義dataset
  def __init__(self , data_path , label_path):
    super().__init__()
    train_txt = open(data_path,'r').readlines()
    train_label_txt = open(label_path,'r').readlines()
    self.train_data = []
    self.train_label = []
    for turns in train_txt:
      sentense = turns.replace('\n','').replace('__eou__' , '')
      self.train_data.append(sentense)
    for turns in train_label_txt:
      label = turns.replace('\n' , '')
      self.train_label.append(int(label) - 1)
  def __len__(self):
    return len(self.train_data)

  def __getitem__(self,idx):
    trainData = self.train_data[idx]
    trainLabel = np.array(self.train_label[idx])
    bert_input = tokenizer(trainData,padding='max_length', max_length = 100, truncation=True, return_tensors="pt")
    return bert_input , trainLabel

class Classifier(nn.Module):
  def __init__(self):
    super(Classifier , self).__init__()
    self.bert = BertModel.from_pretrained('bert-base-cased')
    self.drop = nn.Dropout(0.1)
    self.linear = nn.Linear(768, 10)
    self.relu = nn.ReLU()

  def forward(self , input_id , mask):
    _,output = self.bert(input_ids= input_id, attention_mask=mask,return_dict=False)
    output = self.drop(output)
    output = self.linear(output)
    output = self.relu(output)
    return output

from tqdm import tqdm
def train(model,train_data , lr , epochs):
  train_dataloader = torch.utils.data.DataLoader(train_data, batch_size=32, shuffle=True)
  loss = nn.CrossEntropyLoss()
  optimizer = Adam(model.parameters(), lr= 1e-6)
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

  if torch.cuda.is_available():
    model = model.cuda()
    loss = loss.cuda()
  
  for epoch_num in range(epochs):
    total_acc_train = 0
    total_loss_train = 0
    for train_input, train_label in tqdm(train_dataloader): #每次拿出32筆資料
      train_label = train_label.to(device)
      mask = train_input['attention_mask'].to(device)
      input_id = train_input['input_ids'].squeeze(1).to(device)

      output = model(input_id, mask)
      batch_loss = loss(output, train_label.long()) #算出loss
      total_loss_train += batch_loss.item()          
      acc = (output.argmax(dim=1) == train_label).sum().item()
      total_acc_train += acc
      model.zero_grad()
      batch_loss.backward()
      optimizer.step()

  print(f'Epochs: {epoch_num + 1} | Train Loss: {total_loss_train / len(train_data): .3f} \| Train Accuracy: {total_acc_train / len(train_data): .3f}')
  



model = Classifier()
LR = 1e-6
EPOCH = 10
train_data = Dataset(training_data_path , training_topic_path)
train(model,train_data, LR , EPOCH)

cm = np.zeros([10,10])
def evaluate(model, test_data):

    test_dataloader = torch.utils.data.DataLoader(test_data, batch_size=64)

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    if use_cuda:

        model = model.cuda()
    
    total_acc_test = 0
    with torch.no_grad():

      for test_input, test_label in test_dataloader:

        test_label = test_label.to(device)
        mask = test_input['attention_mask'].to(device)
        input_id = test_input['input_ids'].squeeze(1).to(device)

        output = model(input_id, mask)
        acc = (output.argmax(dim=1) == test_label).sum().item()
        for i in range(64):
          cm[output.argmax(dim=1)[i].item()][test_label[i].item()] += 1
        total_acc_test += acc

    
    print(f'Test Accuracy: {total_acc_test / len(test_data): .3f}')

test_data = Dataset(testing_data_path , testing_topic_path)
evaluate(model, test_data)
print("Confusion Matrix\n" , cm)