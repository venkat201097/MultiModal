from flask import Flask, render_template, request, redirect, url_for
import os
import sys
import pickle
import pandas as pd
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'

# app.config['UPLOAD_FOLDER'] = 'static'
 
def traingenerator():
	curr_bucket = buckets[bucket]
	if curr_bucket>0:
		for i in range(bucket2shot[curr_bucket]):
			train_data[curr_bucket][i*CLASSES_PER_BUCKET:i*CLASSES_PER_BUCKET+CLASSES_PER_BUCKET] = random.sample(train_data[curr_bucket][i*CLASSES_PER_BUCKET:i*CLASSES_PER_BUCKET+CLASSES_PER_BUCKET],CLASSES_PER_BUCKET)
	
	for sample in train_data[curr_bucket]:
		yield sample

def testgenerator():
	global retrieve
	curr_bucket = buckets[bucket]

	i = 0
	retrieve = 'i'
	for sample in random.sample(testaud[curr_bucket],len(testaud[curr_bucket])):
		i+=1
		yield sample,i
	i = 0
	retrieve = 'a'
	for sample in random.sample(testimg[curr_bucket],len(testimg[curr_bucket])):
		i+=1
		yield sample,i

def storetest(form_dict):
	global testsample
	global retrieve
	timespent = form_dict['timespent']
	if retrieve=='i':
		response = list(form_dict)[0][:4]
		sample = testsample[0].split('_')[1].split('/')[-1]
	else:
		# response = form_dict['label']
		response = list(form_dict)[0]
		# print(response,file=sys.stderr)
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
	global sub_id
	with open('static/Data/S{}/test.csv'.format(sub_id),'a+') as fp:
		fp.write('{},{},{},{},{},{},{},{},{}\n'.format(buckets[bucket],retrieve,sample,sampleid,label,labelid,response,responseid,timespent))

@app.route('/')
def home():
	global bucket, buckets, retrieve
	buckets = [0]+random.sample(range(1,NUM_BUCKETS),NUM_BUCKETS-1)
	#buckets = [0,5,4,2,1,3]	
	bucket = 0
	retrieve = 'i'
	return render_template("index.html")

@app.route('/info',methods=['GET','POST'])
def info():
	with open('static/Data/subjects.csv','a+') as fp:
		fp.write('{},{},{},{},{}\n'.format(request.form['id'],request.form['name'],request.form['age'],request.form['gender'],request.form['email']))
	global sub_id
	sub_id = request.form['id']

	if not os.path.isdir('static/Data/S'+request.form['id']):
		os.system('mkdir '+'static/Data/S'+request.form['id'])

	with open('static/Data/S{}/test.csv'.format(sub_id),'w+') as fp:
		fp.write('Session,Test_Phase,Sample,Sample_Id,Label,Label_Id,Response,Response_Id,Time\n')

	with open('static/Data/S{}/train.csv'.format(sub_id),'w+') as fp:
		fp.write('Session,Sample,Sample_Id,Label,Label_Id,PlayCount,Time\n')

	global train_bucket
	train_bucket = traingenerator()
	return render_template('safety.html', session=bucket,sess_type="train")

@app.route('/traininfo',methods=['GET','POST'])
def traininfo():
	global sub_id
	playcount = request.form['playcount']
	timespent = request.form['timespent']
	print('time: ',timespent)
	with open('static/Data/S{}/train.csv'.format(sub_id),'a+') as fp:
		fp.write('{},{}\n'.format(playcount,timespent))

	return redirect(url_for("train"))



@app.route('/train',methods=['GET','POST'])
def train():
	global sub_id
	global bucket
	global train_bucket
	try:
		trainsample = train_bucket.__next__()
		with open('static/Data/S{}/train.csv'.format(sub_id),'a+') as fp:
			sampleid = trainsample[0]
			sample = trainsample[0].split('_')[0].split('/')[-1]
			labelid = trainsample[1]
			label = trainsample[1].split('_')[1].split('/')[-1]
			fp.write('{},{},{},{},{},'.format(buckets[bucket],sample,sampleid,label,labelid))
	except:
		global test_bucket
		test_bucket = testgenerator()
		return render_template("safety.html", session=bucket,sess_type="test")
	return render_template("train.html", image = trainsample[0],label=trainsample[1])

@app.route('/score',methods=['GET','POST'])
def score():
	if bucket==NUM_BUCKETS:
	# if len(buckets)==0:
		return render_template('end.html')
	return render_template('safety.html', session=bucket,sess_type="train")

@app.route('/test',methods=['GET','POST'])
def test():
	global retrieve
	global test_bucket
	if "test" not in request.form:
		storetest(request.form)
	global testsample
	try:
		testsample,curr_index = test_bucket.__next__()
	except:
		global bucket
		bucket+=1
		# bucket = buckets.pop()
		if bucket<NUM_BUCKETS:
		# if len(buckets)>0:
			global train_bucket
			train_bucket = traingenerator()
		global sub_id
		responses = pd.read_csv('static/Data/S{}/test.csv'.format(sub_id))
		curr_resp = responses[responses['Session']==(buckets[bucket-1])]
		num_test = {'i':0,'a':0}
		# print(bucket-1)
		# print(curr_resp)
		scores = {'i':0,'a':0}
		for i,x in curr_resp.iterrows():
			if x['Label']==x['Response']:
				# print('yes')
				scores[x['Test_Phase']]+=1
			num_test[x['Test_Phase']]+=1
		return render_template('score.html',session=bucket,sess_type="train",score_i='{}/{}'.format(scores['i'],num_test['i']),score_a='{}/{}'.format(scores['a'],num_test['a']))
			# return render_template('safety.html', session=bucket,sess_type="train")

	return render_template("test.html", samples= testsample[1:],label=testsample[0],retrieve=retrieve,index=curr_index)

if __name__ == "__main__":
	CLASSES_PER_BUCKET = 10
	NUM_BUCKETS = 7
	buckets = random.sample(range(NUM_BUCKETS),NUM_BUCKETS)
	bucket = 0
	retrieve = 'i'
	bucket2shot = [2,1,2,3,1,2,3]
	testsample=None
	test_bucket = None
	train_bucket = None

	img2lab = pickle.load(open('static/pickles/img2lab_p.pkl','rb'))
	lab2img = {j:i for i,j in img2lab.items()}

	train_data = pickle.load(open('static/pickles/train_p.pkl','rb'))
	testimg = pickle.load(open('static/pickles/imgtest_p.pkl','rb'))
	testaud = pickle.load(open('static/pickles/audtest_p.pkl','rb'))

	app.run(debug=True)
