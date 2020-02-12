import numpy as np
import random
import os
import pickle

buckets = pickle.load(open('buckets.pkl','rb'))
images = pickle.load(open('images.pkl','rb'))
audios = pickle.load(open('audios.pkl','rb'))

#train = pickle.load(open('train_local.pkl','rb'))
img2lab = pickle.load(open('img2lab.pkl','rb'))
#print(train)

for i in images:
    images[i] = ['static/images/'+j.split('/')[-1] for j in images[i]]
for i in audios:
    audios[i] = ['static/audios/{}/{}'.format(j.split('/')[-2],j.split('/')[-1]) for j in audios[i]]

train2 = []

tempimg0 = []
tempaud0 = []
tempimg3 = []
tempaud3 = []
for x,k in enumerate([1,2,3,1,2,3]):
    temp = []
    for j in range(k):
        for i in buckets[x]:
            a = random.sample(images[i],1)[0]
            print(a)
            del images[i][images[i].index(a)]
            b = random.sample(audios[img2lab[i]],1)[0]
            del audios[img2lab[i]][audios[img2lab[i]].index(b)]
            temp.append((a,b))
            if x==0:
                tempimg0.append([a])
                tempaud0.append([b])
            if x==3:
                tempimg3.append([a])
                tempaud3.append([b])
    train2.append(temp)

imgtest = []
audtest = []
for z,bucket in enumerate(buckets):
    tempimg = []
    tempaud = []
    for i in bucket:
        a = random.sample(images[i],1)[0]
        del images[i][images[i].index(a)]
        b = random.sample(audios[img2lab[i]],1)[0]
        del audios[img2lab[i]][audios[img2lab[i]].index(b)]
        tempimg.append([a,b])
        
        a = random.sample(images[i],1)[0]
        del images[i][images[i].index(a)]
        b = random.sample(audios[img2lab[i]],1)[0]
        del audios[img2lab[i]][audios[img2lab[i]].index(b)]
        tempaud.append([b,a])
    
    for x,i in enumerate(bucket):
        for y,j in enumerate(random.sample(bucket[:x]+bucket[x+1:],9)):
            b = random.sample(audios[img2lab[j]],1)[0]
#            del audios[img2lab[j]][audios[img2lab[j]].index(b)]
            tempimg[x].append(b)
        
        for y,j in enumerate(random.sample(bucket[:x]+bucket[x+1:],9)):
            a = random.sample(images[j],1)[0]
#            del images[j][images[j].index(a)]
            tempaud[x].append(a)
        
        tempimg[x][1:] = random.sample(tempimg[x][1:],len(tempimg[x][1:]))
        tempaud[x][1:] = random.sample(tempaud[x][1:],len(tempaud[x][1:]))
    
    if z==0:
        for x,i in enumerate(bucket):
            for y,j in enumerate(random.sample(bucket[:x]+bucket[x:],10)):
                b = random.sample(audios[img2lab[j]],1)[0]
    #            del audios[img2lab[j]][audios[img2lab[j]].index(b)]
                tempimg0[x].append(b)
            
            for y,j in enumerate(random.sample(bucket[:x]+bucket[x:],10)):
                a = random.sample(images[j],1)[0]
    #            del images[j][images[j].index(a)]
                tempaud0[x].append(a)
            
            tempimg0[x][1:] = random.sample(tempimg[x][1:],len(tempimg0[x][1:]))
            tempaud0[x][1:] = random.sample(tempaud[x][1:],len(tempaud0[x][1:]))
            
        tempimg += tempimg0
        tempaud += tempaud0
    
    if z==3:
        for x,i in enumerate(bucket):
            for y,j in enumerate(random.sample(bucket[:x]+bucket[x:],10)):
                b = random.sample(audios[img2lab[j]],1)[0]
    #            del audios[img2lab[j]][audios[img2lab[j]].index(b)]
                tempimg3[x].append(b)
            
            for y,j in enumerate(random.sample(bucket[:x]+bucket[x:],10)):
                a = random.sample(images[j],1)[0]
    #            del images[j][images[j].index(a)]
                tempaud3[x].append(a)
            
            tempimg3[x][1:] = random.sample(tempimg[x][1:],len(tempimg3[x][1:]))
            tempaud3[x][1:] = random.sample(tempaud[x][1:],len(tempaud3[x][1:]))
        tempimg += tempimg3
        tempaud += tempaud3
    
    imgtest.append([tuple(i) for i in tempimg])
    audtest.append([tuple(i) for i in tempaud])

with open('imgtest.pkl','wb+') as fp:
    pickle.dump(imgtest,fp)

with open('audtest.pkl','wb+') as fp:
    pickle.dump(audtest,fp)

with open('train.pkl','wb+') as fp:
    pickle.dump(train2,fp)

def gen():
    for i in [56,2,6,7,2,5,8,9,4,2,21,4,7]:
        yield i
    for i in [67,2,56,68,24]:
        yield i


    

    
