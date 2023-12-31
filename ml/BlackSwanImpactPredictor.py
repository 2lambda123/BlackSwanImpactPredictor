#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Reading news data
import pandas as pd
import numpy as np
from uuid import uuid4
from os import path

CURRENT_DIR = path.dirname(__file__)

data = {
    'amazon': 
        { 
            'news_url': 'https://news.yahoo.com/amazon-pushing-hard-ocean-shipping-200001052.html',
            'historical_news_path': 'news_data/amazon_news.csv',
            'similarities': [0.7791, 0.5986, 0.7309, 0.7061, 0.7184, 0.648, 0.6707, 0.4732, 0.7404, 0.7302, 0.7908, 0.7849, 0.7267, 0.7621, 0.7944, 0.7392, 0.5898]
        },
    'tradewar':{
            'news_url':'https://www.reuters.com/article/us-usa-trade-china-jobs/u-s-china-trade-war-has-cost-up-to-245000-u-s-jobs-business-group-study-idUSKBN29J2O9',
            'historical_news_path':'news_data/tradewar.csv',
            'similarities':[0.7752, 1.0, 0.458, 0.718, 0.7178, 0.7776]
    },
    'fedhikerates':{
            'news_url':'https://www.theguardian.com/business/2018/dec/19/federal-reserve-interest-rates-raised-trump',
            'historical_news_path':'news_data/fedhikerates.csv',
            'similarities':[0.746, 1.0, 0.5033, 0.7413, 0.716, 0.7886, 0.8383]
    }
} 

use_cached_data = True;
data_type = 'tradewar'
token = '3e609e553c274103bf2acd8dd9029d8c'

def process_URL(news_type):
    global data

    #url of the news to be analysed
    print(news_type)
    print
    data_type = news_type
    news_url = data[data_type]['news_url']


    # In[2]:


    #Sentiment analysis of the news
    import requests

    url = 'https://api.dandelion.eu/datatxt/sent/v1/?lang=en&token=' + token + '&url=' + news_url
    response = requests.get(url)
    res_json = response.json()
    if 'sentiment' in res_json:
        print("Sentiment of the news article:", res_json['sentiment'])


    # In[3]:


    #Read historical news

    news_data = pd.read_csv(data[data_type]['historical_news_path'],sep=";")
    news_data['Date'] = pd.to_datetime(news_data['Date']).dt.date
    # news_data.to_csv('news_data/fedhikerates.csv',sep=";",index=False,columns=news_data.columns)
    news_data.head()


    # In[4]:


    # Find similarities of current news and historical news
    similarities = []

    if not use_cached_data:
        for url in news_data['Link']:
            url = 'https://api.dandelion.eu/datatxt/sim/v1/?url1=' + news_url + '&url2=' + url + '&token=' + token
            response = requests.get(url)
            json_data = response.json()
        #     print(data)
            if('similarity' in json_data):
                similarities.append(json_data['similarity'])
    else:
        similarities = data[data_type]['similarities']
            
    print(similarities)
    print("Mean of similarities: ", np.mean(similarities))


    # In[5]:


    #Get the stock data for the date range of the news

    stock_data = pd.read_csv('stock_data/spy500_historical_data.csv', sep=',')
    stock_data.rename(columns={'Close/Last':'Close'}, inplace=True)
    stock_data['Change_Stock'] = stock_data['Close'].diff(periods=-1)
    stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.date
    stock_data = stock_data.drop(columns=['Volume', 'Open', 'High' ,'Low'])

    stock_data.head()


    # In[6]:


    #Plot a graph of history with changes as per news

    merged_data = pd.merge(stock_data, news_data, on = "Date" )
    merged_data.drop_duplicates(subset="Date", keep='last', inplace=True)
    merged_data.set_index('Date', inplace=True)
    # merged_data['Change_Stock'].loc[(merged_data['Change_Stock'] > 0)] = -1
    merged_data


    # In[7]:


    from datetime import datetime, timedelta
    import plotly.graph_objs as go
    from chart_studio import plotly as py
    import cufflinks as cf
    cf.go_offline()
    from plotly.offline import download_plotlyjs, init_notebook_mode, plot,iplot


    dateset= list(sorted(merged_data.index))

    changelist = []
    for date in dateset:
        try:
            changelist.append(merged_data.loc[date]['Change_Stock'].round(3))
        except:
            changelist.append(0)

    trace_close = go.Scatter(
                    x=stock_data["Date"],
                    y=stock_data['Close'],
                    name = "Close")

    colorlist = []
    for s in changelist:
        if s > 0:
            colorlist.append('green')
        elif s == 0:
            colorlist.append('rgb(150, 150, 150)')
        else:
            colorlist.append('red')
            
    shapes = [dict(
                x0 = s,
                x1 = s + timedelta(days=1),
                y0 = 0,
                y1 = 1,
                xref= 'x',
                yref = 'paper',
                opacity =  0.3,
                line = {'color': colorlist[i], 'width': 5}
                ) for (i,s) in enumerate(dateset)]


    annotations =  [dict(
                x = s,
                y = (0.05 + i*0.2) % 1,
                xref = 'x',
                yref = 'paper',
                showarrow = False,
                xanchor = 'left',
                ax = 20,
                ay = -30,
                bordercolor = '#000000',
                borderwidth = 2,
                borderpad = 4,
                bgcolor = colorlist[i],
                font = {
                    'family':'Courier New, monospace',
                    'size':16,
                    'color':'#ffffff'
                },
                opacity = 0.8,
                text =  changelist[i]
                
                ) for (i,s) in enumerate(dateset)]


    fig_data = [trace_close]

    layout = dict(
        title = "Stock prices",
        shapes = shapes,
        annotations = annotations,
        xaxis = dict(range = [merged_data.index.min() - pd.DateOffset(months=2),merged_data.index.max() + pd.DateOffset(months=2)]),
        yaxis = dict(title = 'Close price')
    )

    fig = dict(data=fig_data, layout=layout)
    filename = f'{uuid4()}.png'
    go.Figure(fig).write_image(f'{CURRENT_DIR}static/{filename}')
    # go.Figure(fig).show()


    # In[12]:


    # Calculate t-test

    """
    https://www.statisticshowto.com/probability-and-statistics/t-test/
    How big is “big enough”? 
    Every t-value has a p-value to go with it. 
    A p-value is the probability that the results from your sample data occurred by chance. 
    For example, a p value of 5% is 0.05. Low p-values are good; They indicate your data did not occur by chance. 
    For example, a p-value of .01 means there is only a 1% probability that the results from an experiment happened by chance. 
    In most cases, a p-value of 0.05 (5%) is accepted to mean the data is valid.
    """

    from scipy import stats

    historical_news_dates =  list(sorted(merged_data.index))

    min_date = min(historical_news_dates) - pd.DateOffset(months=2)
    max_date = max(historical_news_dates) + pd.DateOffset(months=2)
    relevant_stock_data = stock_data[(stock_data["Date"] >= min_date)  & (stock_data["Date"] <= max_date)]
    relevant_stock_data.set_index('Date', inplace=True)
    relevant_stock_dates = list(relevant_stock_data.index)


    remaining_dates = set(relevant_stock_dates) - set(historical_news_dates)

    # print(len(relevant_stock_dates), len(historical_news_dates), len(remaining_dates))

    b = list(relevant_stock_data.loc[historical_news_dates]["Change_Stock"])
    a = list(relevant_stock_data.loc[remaining_dates]["Change_Stock"])

    _, p2 = stats.ttest_ind(a,b,equal_var = True)
    impact_score = (10 - p2*10).round(1)
    sentiment = res_json['sentiment']['type'].capitalize()

    print("t-statistics =", p2)
    print("Impact score =", impact_score)
    print("Sentiment = ", sentiment)

    return (filename, impact_score, sentiment)



# print(process_URL('amazon'))
# print(process_URL('tradewar'))
# print(process_URL('fedhikerates'))