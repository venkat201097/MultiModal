from flask import Flask, render_template, request, redirect, url_for#, session
import pickle
import pandas as pd
import random
#from google.cloud import storage

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.secret_key = '546781ui2njr16i7ohdnf12gv3fu$%^#@'


def upload_to_cloud(source_file_name, destination_blob_name, bucket_name='multimodal-mapping-259008.appspot.com'):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)


def download_from_cloud(source_blob_name, destination_file_name, bucket_name='multimodal-mapping-259008.appspot.com'):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)


def getsession():
    session = pickle.load(open('/tmp/S17_session.pkl', 'rb'))
    return session


def storesession(session):
    pickle.dump(session, open('/tmp/S17_session.pkl', 'wb+'))


def traingenerator(session):
    #session = getsession()
    CLASSES_PER_BUCKET = session['CLASSES_PER_BUCKET']
    bucket2shot = session['bucket2shot']
    buckets = session['buckets']
    bucket = session['bucket']
    train_data = pickle.load(open('static/pickles/train_p.pkl', 'rb'))
    curr_bucket = buckets[bucket]
    if curr_bucket > 0:
        for i in range(bucket2shot[curr_bucket]):
            train_data[curr_bucket][i*CLASSES_PER_BUCKET:i*CLASSES_PER_BUCKET+CLASSES_PER_BUCKET] = random.sample(train_data[curr_bucket][i*CLASSES_PER_BUCKET:i*CLASSES_PER_BUCKET+CLASSES_PER_BUCKET], CLASSES_PER_BUCKET)
    return train_data[curr_bucket]


def testgenerator(session):
    #session = getsession()
    retrieve = session['retrieve']
    buckets = session['buckets']
    bucket = session['bucket']
    curr_bucket = buckets[bucket]
    testimg = pickle.load(open('static/pickles/imgtest_p.pkl', 'rb'))
    testaud = pickle.load(open('static/pickles/audtest_p.pkl', 'rb'))
    if retrieve == 'i':
        return list(zip(random.sample(testaud[curr_bucket], len(testaud[curr_bucket])), range(1, len(testaud[curr_bucket])+1)))
    else:
        return list(zip(random.sample(testimg[curr_bucket], len(testimg[curr_bucket])), range(1, len(testimg[curr_bucket])+1)))


def storetest(form_dict,session):
    #session = getsession()
    testsample = session['testsample']
    retrieve = session['retrieve']
    timespent = form_dict['timespent']
    img2lab = pickle.load(open('static/pickles/img2lab_p.pkl', 'rb'))
    lab2img = {j: i for i, j in img2lab.items()}
    if retrieve == 'i':
        response = [i for i in list(form_dict) if i != 'timespent'][0][:4]
        sample = testsample[0].split('_')[1].split('/')[-1]
    else:
        # response = form_dict['label']
        response = [i for i in list(form_dict) if i != 'timespent'][0]
        # print(response,file=sys.stderr)
        print(testsample[0])
        sample = testsample[0].split('_')[0].split('/')[-1]
    sampleid = testsample[0]
    if retrieve == 'i':
        label = lab2img[sample]
    else:
        label = img2lab[sample]
    for i in testsample[1:]:
        if retrieve == 'i':
            if i.split('_')[0].split('/')[-1] == lab2img[sample]:
                labelid = i
            if i.split('_')[0].split('/')[-1] == response:
                responseid = i
        else:
            if i.split('_')[1].split('/')[-1] == img2lab[sample]:
                labelid = i
            if i.split('_')[1].split('/')[-1] == response:
                responseid = i
    with open('/tmp/S{}_test.csv'.format(session['sub_id']), 'a+') as fp:
        fp.write('{},{},{},{},{},{},{},{},{}\n'.format(session['buckets'][session['bucket']], retrieve, sample, sampleid, label, labelid, response, responseid, timespent))


def new_session():
    NUM_BUCKETS = 7
    session = {}
    session['new'] = 'no'
    session['CLASSES_PER_BUCKET'] = 10
    session['NUM_BUCKETS'] = NUM_BUCKETS
    session['buckets'] = [0]+random.sample(range(1, NUM_BUCKETS), NUM_BUCKETS-1)
    session['bucket'] = 0
    session['retrieve'] = 'i'
    session['bucket2shot'] = [2, 1, 2, 3, 1, 2, 3]
    session['testsample'] = None
    session['test_bucket'] = None
    session['train_bucket'] = None
    return session


@app.route('/')
def home():
    # print(session.keys())
    # if 'new' not in session:
    session = new_session()
    print(session.keys())
    print(session['buckets'], session['bucket'])
    storesession(session)
    return render_template('index.html')


@app.route('/info', methods=['GET', 'POST'])
def info():
    session = getsession()
    #download_from_cloud('subjects.csv', '/tmp/subjects.csv')
    with open('/tmp/subjects.csv', 'a+') as fp:
        fp.write('{},{},{},{},{}\n'.format(request.form['id'], request.form['name'], request.form['age'], request.form['gender'], request.form['email']))
    #upload_to_cloud('/tmp/subjects.csv', 'subjects.csv')
    sub_id = request.form['id']
    session['sub_id'] = sub_id

    with open('/tmp/S{}_test.csv'.format(sub_id), 'w+') as fp:
        fp.write('Session,Test_Phase,Sample,Sample_Id,Label,Label_Id,Response,Response_Id,Time\n')

    with open('/tmp/S{}_train.csv'.format(sub_id), 'w+') as fp:
        fp.write('Session,Sample,Sample_Id,Label,Label_Id,PlayCount,Time\n')

    # global train_bucket
    session['train_bucket'] = traingenerator(session)
    storesession(session)
    return render_template('safety.html', session=session['bucket'], sess_type="train")


@app.route('/traininfo', methods=['GET', 'POST'])
def traininfo():
    session = getsession()
    sub_id = session['sub_id']
    playcount = request.form['playcount']
    timespent = request.form['timespent']

    with open('/tmp/S{}_train.csv'.format(sub_id), 'a+') as fp:
        fp.write('{},{}\n'.format(playcount, timespent))

    return redirect(url_for("train"))


@app.route('/train', methods=['GET', 'POST'])
def train():
    session = getsession()
    print('train', session['train_bucket'], session.keys())
    sub_id = session['sub_id']
    bucket = session['bucket']
    buckets = session['buckets']
    # global train_bucket
    try:
        # train_bucket = session['train_bucket']
        # trainsample = train_bucket.pop(0)
        # session['train_bucket'] = train_bucket
        trainsample = session['train_bucket'].pop(0)
        # session.modified = True
        with open('/tmp/S{}_train.csv'.format(sub_id), 'a+') as fp:
            sampleid = trainsample[0]
            sample = trainsample[0].split('_')[0].split('/')[-1]
            labelid = trainsample[1]
            label = trainsample[1].split('_')[1].split('/')[-1]
            fp.write('{},{},{},{},{},'.format(buckets[bucket], sample, sampleid, label, labelid))
    except:
        # global test_bucket
        session['test_bucket'] = testgenerator(session)
        storesession(session)
        return render_template("safety.html", session=bucket, sess_type="test")
    storesession(session)
    return render_template("train.html", image=trainsample[0], label=trainsample[1])


@app.route('/score', methods=['GET', 'POST'])
def score():
    session = getsession()
    if session['bucket'] == session['NUM_BUCKETS']:
        upload_to_cloud('/tmp/S{}_train.csv'.format(session['sub_id']), 'S{}_train.csv'.format(session['sub_id']))
        upload_to_cloud('/tmp/S{}_test.csv'.format(session['sub_id']), 'S{}_test.csv'.format(session['sub_id']))
        return render_template('end.html')
    return render_template('safety.html', session=session['bucket'], sess_type="train")


@app.route('/test', methods=['GET', 'POST'])
def test():
    session = getsession()
    # global test_bucket
    if "test" not in request.form:
        storetest(request.form,session)
    # global testsample
    try:
        test_bucket = session['test_bucket']
        testsample, curr_index = test_bucket.pop(0)
        session['test_bucket'] = test_bucket
        session['testsample'] = testsample
    except:
        print('except bruh')
        if session['retrieve'] == 'i':
            print('yup')
            session['retrieve'] = 'a'
            session['test_bucket'] = testgenerator(session)
            test_bucket = session['test_bucket']
            testsample, curr_index = test_bucket.pop(0)
            session['test_bucket'] = test_bucket
            session['testsample'] = testsample
        else:
            session['retrieve'] = 'i'
            # global bucket
            session['bucket'] += 1
            # session.modified = True
            bucket = session['bucket']
            NUM_BUCKETS = session['NUM_BUCKETS']
            # bucket = buckets.pop()
            if bucket < NUM_BUCKETS:
                session['train_bucket'] = traingenerator(session)
            sub_id = session['sub_id']
            responses = pd.read_csv('/tmp/S{}_test.csv'.format(sub_id))
            print(session['sub_id'], responses)
            curr_resp = responses[responses['Session'] == (session['buckets'][bucket-1])]
            num_test = {'i': 0, 'a': 0}
            # print(bucket-1)
            # print(curr_resp)
            scores = {'i': 0, 'a': 0}
            for i, x in curr_resp.iterrows():
                if x['Label'] == x['Response']:
                    # print('yes')
                    scores[x['Test_Phase']] += 1
                num_test[x['Test_Phase']] += 1
            storesession(session)
            return render_template('score.html', session=bucket, sess_type="train", score_i='{}/{}'.format(scores['i'], num_test['i']), score_a='{}/{}'.format(scores['a'], num_test['a']))
    storesession(session)
    return render_template("test.html", samples=testsample[1:], label=testsample[0], retrieve=session['retrieve'], index=curr_index)


if __name__ == "__main__":
    app.run(debug=True)
