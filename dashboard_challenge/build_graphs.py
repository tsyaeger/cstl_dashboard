import json
import numpy as np
import pandas as pd
from pandas import Series, DataFrame
from pandas.io.json import json_normalize 
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap 
import seaborn as sns
 
# GRAPH SPECS
dpi = 250
titlesize = 24
labelsize = 17
plt.style.use('dark_background')


def build_graphs(file):
	df = create_df(read_data(file))
	get_state_counts(df)
	get_risk_counts(df)
	get_us_risk(df)
	get_country_risk(df)

def read_data(file):
	print("building")
	with open(file, 'r') as f:
	    return json.load(f)

def create_df(data):
	# UNPACK JSON
	df_norm = pd.io.json.json_normalize(data)
	device_norm = pd.io.json.json_normalize(
		data, 
		record_path='devices', 
		meta='id', 
		record_prefix='devices.'
	)
	df = pd.merge(device_norm, df_norm, on="id")

	# TRIM COLUMNS
	df = df[[
		'id', 
		'risk',
		'devices.created_at', 
		'devices.risk', 
		'devices.state', 
		'devices_count', 
		'last_location.location.country',
		'last_location.location.region', 
		]]

	df['created_at'] = pd.to_datetime(df["devices.created_at"]).dt.date
	df = df.sort_values("created_at", ascending=False)
	df['last_location.location.country'] = df['last_location.location.country'].replace({'United Arab Emirates':'UAE'})
	
	# ADD RISK CATEGORY COLUMN BASED ON RISK VALUE
	df.loc[df.risk <= 0.6, 'risk_category'] = 'safe'
	df.loc[(df.risk > 0.6) & (df.risk < 0.9), 'risk_category'] = 'suspicious'
	df.loc[df.risk >= 0.9, 'risk_category'] = 'malicious'
	return df


def make_stackplot(labels, title, filename, *args):
	fig, ax = plt.subplots(1,1, figsize=(12, 8), dpi=dpi)
	fig.suptitle(title, fontsize=titlesize)
	plt.xlabel('')
	plt.ylabel('')
	ax.stackplot(*args, labels=labels)
	ax.xaxis_date()
	fig.autofmt_xdate()
	ax.xaxis.set_tick_params(labelsize=labelsize)
	ax.yaxis.set_tick_params(labelsize=labelsize)
	ax.legend(loc='upper left', prop={'size': 22})
	plt.savefig(filename, bbox_inches='tight')

def make_heatmap(data, title, filename):
	fig, ax = plt.subplots(1,1, figsize=(11,16), dpi=dpi)
	ax.set_title(title, fontsize=22, y=1.03)
	sns.heatmap(data, annot_kws={"size": 18}, xticklabels=False)
	ax.set_ylabel('')    
	plt.savefig(filename, bbox_inches='tight')


def get_state_counts(df):
	# TIMESERIES STATE COUNTS - PIVOT
	ts_state_df = pd.pivot_table(
		df, 
		index='created_at', 
		columns='devices.state', 
		values='last_location.location.country', 
		aggfunc='size', 
		fill_value=0
	)
	ts_state_df = ts_state_df[['unapproved', 'approved']]

	# TIMESERIES STATE COUNTS - STACKED BAR PLOT 
	labels = ['unapproved', 'approved']
	title = 'Daily Count By Outcome'
	filename = "static/images/ts_state_stackplot.png"
	args = [ts_state_df.index, ts_state_df.unapproved, ts_state_df.approved]
	make_stackplot(labels, title, filename, *args)

def get_risk_counts(df):
	# TIMESERIES RISK COUNTS
	risk_df = pd.pivot_table(
		df, 
		index='created_at', 
		columns="risk_category",
		values='risk', 
		aggfunc='size', 
		fill_value=0
	)
	# TIMESERIES RISK COUNTS - STACKED BAR PLOT
	labels = ['safe', 'suspicious', 'malicious']
	title = 'Daily Count By Risk Level'
	filename = "static/images/ts_risk_stackplot.png"
	args = [risk_df.index, risk_df.safe,  risk_df.suspicious, risk_df.malicious]
	make_stackplot(labels, title, filename, *args)

def sort_by_risk(df):
	# NEW DF SORTED BY RISK
	risk_df = df[['last_location.location.country', "last_location.location.region", 'risk']]
	risk_df = risk_df.sort_values("risk", ascending=False)
	return risk_df

def get_us_risk(df):
	risk_df = sort_by_risk(df)
	# GBY US REGIONS MEAN RISK
	us_df = risk_df[risk_df['last_location.location.country'] == 'United States'].dropna()
	us_df = us_df.groupby("last_location.location.region")["risk"].agg(['mean', 'size']) 
	us_df = us_df.where(us_df["size"] > 3).dropna() 
	us_graph_df = us_df[['mean']]
	us_graph_df.sort_values('mean', ascending=False, inplace=True)

	make_heatmap(
		us_graph_df, 
		"Average Risk By State", 
		"static/images/usregion_risk_heattest.png"
	)

def get_country_risk(df):
	risk_df = sort_by_risk(df)
	# GBY COUNTRIES MEAN RISK
	country_df = risk_df.groupby("last_location.location.country")["risk"].agg(['mean', 'size'])
	country_df = country_df.where(country_df["size"] > 3).dropna()
	country_df.sort_values('mean', ascending=False, inplace=True)
	country_graph_df = country_df[['mean']]

	make_heatmap(
		country_graph_df, 
		"Average Risk By Country", 
		"static/images/country_risk_heatmap.png"
	)



