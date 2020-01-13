from flask import Flask, render_template, request, redirect, url_for
import os
import sys
import pickle
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'

# app.config['UPLOAD_FOLDER'] = 'static'
 
def traingenerator():
	for sample in train_data[bucket]:
		yield sample

def testgenerator():
	global retrieve
	retrieve = 'i'
	for sample in testaud[bucket]:
		yield sample
	retrieve = 'a'
	for sample in testimg[bucket]:
		yield sample

def storetest(form_dict):
	global testsample
	global retrieve
	if retrieve=='i':
		response = list(form_dict)[0][:4]
		sample = testsample[0].split('_')[1].split('/')[-1]
	else:
		# response = form_dict['label']
		response = list(form_dict)[0]
		print(response,file=sys.stderr)
		sample = testsample[0].split('_')[0].split('/')[-1]
	sampleid = testsample[0]
	if retrieve=='i':
		label = lab2img[sample]
	else:
		label = img2lab[sample]
	for i in testsample[1:]:
		if retrieve=='i':
			if i.split('_')[0].split('/')[-1]==lab2img[sample]:
				labelid = i
			if i.split('_')[0].split('/')[-1]==response:
				responseid = i
		else:
			if i.split('_')[1].split('/')[-1]==img2lab[sample]:
				labelid = i
			if i.split('_')[1].split('/')[-1]==response:
				responseid = i

	with open('static/Data/subject_0.csv','a+') as fp:
		fp.write('{},{},{},{},{},{},{},{}\n'.format(bucket,retrieve,sample,sampleid,label,labelid,response,responseid))

@app.route('/')
def home():
	global bucket,retrieve
	bucket = 0
	retrieve = 'i'
	return render_template("index.html")

@app.route('/info',methods=['GET','POST'])
def info():
	with open('static/Data/subjects.csv','a+') as fp:
		fp.write('{},{},{}\n'.format(request.form['name'],request.form['gender'],request.form['email']))
	global train_bucket
	train_bucket = traingenerator()
	return render_template('safety.html', session=bucket,sess_type="train")

@app.route('/train',methods=['GET','POST'])
def train():
	global bucket
	global train_bucket
	try:
		trainsample = train_bucket.__next__()
	except:
		global test_bucket
		test_bucket = testgenerator()
		return render_template("safety.html", session=bucket,sess_type="test")
	return render_template("train.html", image = trainsample[0],label=trainsample[1])

@app.route('/test',methods=['GET','POST'])
def test():
	global retrieve
	global test_bucket
	if "test" not in request.form:
		storetest(request.form)
	global testsample
	try:
		testsample = test_bucket.__next__()
	except:
		global bucket
		bucket+=1
		if bucket==NUM_BUCKETS:
			return render_template('end.html')
		else:
			global train_bucket
			train_bucket = traingenerator()
			return render_template('safety.html', session=bucket,sess_type="train")

	return render_template("test.html", samples= testsample[1:],label=testsample[0],retrieve=retrieve,proceed="hidden")

if __name__ == "__main__":
	CLASSES_PER_BUCKET = 10
	NUM_BUCKETS = 6
	bucket = 5
	retrieve = 'i'

	testsample=None
	test_bucket = None
	train_bucket = None

	img2lab = pickle.load(open('static/pickles/img2lab.pkl','rb'))
	lab2img = {j:i for i,j in img2lab.items()}

	train_data = pickle.load(open('static/pickles/train.pkl','rb'))
	testimg = pickle.load(open('static/pickles/imgtest.pkl','rb'))
	testaud = pickle.load(open('static/pickles/audtest.pkl','rb'))

	app.run(debug=True)