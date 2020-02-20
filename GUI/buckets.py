import random
import numpy as np
a = np.array([random.sample([0,3],2),random.sample([1,4],2),random.sample([2,5],2)])
h1 = random.sample(list(a[:,0]),3)
h2 = random.sample(list(a[:,1]),3)

with open('order','a+') as fp:
	fp.write('\n'.join(list(map(str,h1+h2))))