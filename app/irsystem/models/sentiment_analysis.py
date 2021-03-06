import os
import numpy as np
import pandas as pd
from collections import Counter
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import math
import json
import re
from nltk.stem import PorterStemmer
import nltk.classify.util
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import movie_reviews

with open(os.path.join(os.getcwd(),'korean_user_reviews.json')) as fp4:
    reviews_dict = json.load(fp4)

def map_network(network,x):
    if x == network:
        return 1
    else:
        return 0
replace_no_space = re.compile("(\.)|(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\()|(\))|(\[)|(\])|(\d+)")
replace_with_space =re.compile("(<br\s*/><br\s*/>)|(\-)|(\/)")
no_space = ""
blankspace = " "
replace_no_space = re.compile("(\")|(\d+)")
replace_with_space =re.compile("(<br\s*/><br\s*/>)|(\-)|(\/)")
no_space = ""
blankspace = " "
def preprocess_reviews(datas):
    for index in datas:
        if len(datas[index])==0:
                datas[index] = []
        else:
            datas[index] = [replace_no_space.sub(no_space, line) for line in datas[index]]
            datas[index] = [replace_with_space.sub(blankspace, line) for line in datas[index]]

    return datas
datas = preprocess_reviews(reviews_dict)
nltk.download('movie_reviews')

def extract_features(word_list):
    return dict([(word, True) for word in word_list])
positive_fileids = movie_reviews.fileids('pos')
negative_fileids = movie_reviews.fileids('neg')
features_positive = [(extract_features(movie_reviews.words(fileids=[f])),
                     'Positive') for f in positive_fileids]
features_negative = [(extract_features(movie_reviews.words(fileids=[f])),
                     'Negative') for f in negative_fileids]
threshold_factor = 0.8
threshold_positive = int(threshold_factor * len(features_positive))
threshold_negative = int(threshold_factor * len(features_negative))
features_train = features_positive[:threshold_positive] + features_negative[:threshold_negative]
features_test = features_positive[threshold_positive:] + features_negative[threshold_negative:]
classifier = NaiveBayesClassifier.train(features_train)

def get_sentiment(datas):
    sentiment_dict = {}
    for index in datas:
        if len(datas[index])==0:
            sentiment_dict[index] = [{'Reviews': 'N/A', 'Sentiment': 'Positive', 'Probability': 0.0}]
        for review in datas[index]:
            probdist = classifier.prob_classify(extract_features(review.split()))
            if index in sentiment_dict:
                sentiment_dict[index].append({'Reviews': review, 'Sentiment': probdist.max(), 'Probability': round(probdist.prob(probdist.max()), 2)})
            else:
                sentiment_dict[index] = [{'Reviews': review, 'Sentiment': probdist.max(), 'Probability': round(probdist.prob(probdist.max()), 2)}]
    return sentiment_dict

sentiment_dict = get_sentiment(datas)

def get_sentiment_scores_dict(sentiment_dict):
    sentiment_scores_dict = {}
    for index in sentiment_dict:
        sentiment_scores_list = []
        for element in sentiment_dict[index]:
            if element['Sentiment'] == 'Negative':
                sentiment_scores_list.append(element['Probability'] * (-1.0))
            else:
                sentiment_scores_list.append(element['Probability'])
        sentiment_scores_dict[index] = sentiment_scores_list 
    return sentiment_scores_dict
sentiment_scores_dict = get_sentiment_scores_dict(sentiment_dict)

def get_high_low_reviews(sentiment_dict, sentiment_scores_dict):
    high_low_reviews = {}
    for index in sentiment_dict:
        if len(sentiment_scores_dict[index])==0:
            high_low_reviews[index] = {'Highest Sentiment Review': "None", 'Lowest Sentiment Review': "None"}
        elif len(sentiment_scores_dict[index]) == 1:
            if sentiment_dict[index][0]['Sentiment'] =='Negative':
                high_low_reviews[index] = {'Highest Sentiment Review': "None", 'Lowest Sentiment Review': sentiment_dict[index][0]['Reviews']}
            else:
                high_low_reviews[index] = {'Highest Sentiment Review': sentiment_dict[index][0]['Reviews'], 'Lowest Sentiment Review': "None"}
        elif sentiment_scores_dict[index].count(sentiment_scores_dict[index][0]) == len(sentiment_scores_dict[index]):
            if sentiment_dict[index][0]['Sentiment'] =='Negative':
                high_low_reviews[index] = {'Highest Sentiment Review': "None", 'Lowest Sentiment Review': sentiment_dict[index][0]['Reviews']}
            else:
                high_low_reviews[index] = {'Highest Sentiment Review': sentiment_dict[index][0]['Reviews'], 'Lowest Sentiment Review': "None"}
        else:
            lst = sentiment_scores_dict[index]
            min_index = lst.index(min(lst))
            max_index = lst.index(max(lst))
            high_low_reviews[index] = {'Highest Sentiment Review': sentiment_dict[index][max_index]['Reviews'], 'Lowest Sentiment Review': sentiment_dict[index][min_index]['Reviews']}
    return high_low_reviews

high_low_reviews = get_high_low_reviews(sentiment_dict, sentiment_scores_dict)
def get_sentiment_score(sentiment_dict):
    sentiment_scores = {}
    for index in sentiment_dict:
        sum = 0
        for element in sentiment_dict[index]:
            if element['Sentiment'] == 'Negative':
                sum -= element['Probability']
            else:
                sum += element['Probability']
        sentiment_scores[index] = sum/len(sentiment_dict[index])
    return sentiment_scores
sentiment_scores = get_sentiment_score(sentiment_dict)
def get_reviews_and_sentiment(datas, sentiment_scores):
    reviews_sent = {}
    for key in datas: 
        if (len(datas[key]) == 0):
            reviews_sent[key] = {'Predicted Sentiment': 'Neutral', 'Sentiment Score': 0.0, 'High Sentiment Review': 'None', 'Lowest Sentiment Review': 'None', 'Reviews': 'There are no reviews for this drama.'}
        elif (sentiment_scores[key]==0.0 and len(datas[key]) > 0):
            if len(datas[key]) < 5:
                reviews_sent[key] = {'Predicted Sentiment': 'Neutral', 'Sentiment Score': sentiment_scores[key], 'Highest Sentiment Review': high_low_reviews[key]['Highest Sentiment Review'], 'Lowest Sentiment Review': high_low_reviews[key]['Lowest Sentiment Review'], 'Reviews': datas[key]}
            else:
                reviews_sent[key] = {'Predicted Sentiment': 'Neutral', 'Sentiment Score': sentiment_scores[key], 'Highest Sentiment Review': high_low_reviews[key]['Highest Sentiment Review'], 'Lowest Sentiment Review': high_low_reviews[key]['Lowest Sentiment Review'], 'Reviews': datas[key][:5]}
        elif len(datas[key]) < 5: 
            if (sentiment_scores[key] < 0): 
                reviews_sent[key] = {'Predicted Sentiment': 'Negative', 'Sentiment Score': abs(sentiment_scores[key]), 'Highest Sentiment Review': high_low_reviews[key]['Highest Sentiment Review'], 'Lowest Sentiment Review': high_low_reviews[key]['Lowest Sentiment Review'], 'Reviews': datas[key]}
            else: 
                reviews_sent[key] = {'Predicted Sentiment': 'Positive', 'Sentiment Score': sentiment_scores[key], 'Highest Sentiment Review': high_low_reviews[key]['Highest Sentiment Review'], 'Lowest Sentiment Review': high_low_reviews[key]['Lowest Sentiment Review'], 'Reviews': datas[key]}
        else: 
            if (sentiment_scores[key] < 0): 
                reviews_sent[key] = {'Predicted Sentiment': 'Negative', 'Sentiment Score': abs(sentiment_scores[key]), 'Highest Sentiment Review': high_low_reviews[key]['Highest Sentiment Review'], 'Lowest Sentiment Review': high_low_reviews[key]['Lowest Sentiment Review'], 'Reviews': datas[key][:5]}
            else: 
                reviews_sent[key] = {'Predicted Sentiment': 'Positive', 'Sentiment Score': sentiment_scores[key], 'Highest Sentiment Review': high_low_reviews[key]['Highest Sentiment Review'], 'Lowest Sentiment Review': high_low_reviews[key]['Lowest Sentiment Review'], 'Reviews': datas[key][:5]}
    return reviews_sent 
reviews_sent = get_reviews_and_sentiment(datas, sentiment_scores)
with open('sentiment_analysis.json', 'w') as fp:
    json.dump(sentiment_scores, fp)
with open('reviews_sentiment.json', 'w') as fp:
    json.dump(reviews_sent, fp)
with open('high_low_reviews.json', 'w') as fp:
    json.dump(high_low_reviews, fp) 
