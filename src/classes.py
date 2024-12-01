import sys

from math import *
from datetime import datetime

import cplex
from cplex.callbacks import LazyConstraintCallback
from cplex.callbacks import UserCutCallback

# class for loggin the screen output also into file

class Logger(object):
    def __init__(self, outdir):
        self.terminal = sys.stdout
        self.log = open(outdir + "/" + "bison.log", "w+", buffering=1)  # Line buffering

    def write(self, message):
        if message != '\n':
            message = datetime.now().strftime('%Y-%m-%d %H-%M-%S : ') + message
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # Ensure writing to file immediately

    def flush(self):
        # this flush method is needed for cplex compatibility.
        # we should flush the log file while keeping cplex compatibility
        self.log.flush()
        self.terminal.flush()

    def __del__(self):
        # Ensure the log file is properly closed when the Logger is destroyed
        if hasattr(self, 'log'):
            self.log.close()
		
# class for nice terminal output
class color:
	PURPLE 		= '\033[95m'
	CYAN 		= '\033[96m'
	DARKCYAN 	= '\033[36m'
	BLUE 		= '\033[94m'
	GREEN 		= '\033[92m'
	YELLOW 		= '\033[93m'
	RED 		= '\033[91m'
	BOLD 		= '\033[1m'
	UNDERLINE 	= '\033[4m'
	END 		= '\033[0m'
	
# ---------------------------------------------------
# --- Lazy Cut Callback (for Rodrigues et al., 2014)
# ---------------------------------------------------

class LazyCallback(LazyConstraintCallback):

	def __call__(self, instance, ocean, detection_prob, s, r, c, theta):
		self.number_of_calls += 1

		# get incumbent solution values

		value_of_s = {}
		value_of_r = {}

		for gx,gy in ocean:
			value_of_s[gx,gy] = self.get_values(s[gx,gy])
			value_of_r[gx,gy] = self.get_values(r[gx,gy])

		if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
			value_of_c = {}
			for tx,ty in ocean:
				value_of_c[tx,ty] = self.get_values(c[tx,ty])

		# sorting

		sort_me = []

		for gx,gy in ocean:
			sort_me.append((gx,gy,'s',value_of_s[gx,gy]))
			sort_me.append((gx,gy,'r',value_of_r[gx,gy]))

		sort_me = sorted(sort_me, key=lambda sort_me: sort_me[3], reverse=True)
		n = len(sort_me)

		# compute permutation

		pi = [(0,0,0,0)]

		for i in range(1,n+1):
			pi.append((sort_me[i-1][0],sort_me[i-1][1],sort_me[i-1][2]))

		for tx,ty in ocean:
			# compute cut strength

			lhs = 0

			for i in range(2,n+1):
				var_i = pi[i][2]
				pi_i_x = pi[i][0]
				pi_i_y = pi[i][1]

				for j in range(1,i):
					var_j = pi[j][2]
					pi_j_x = pi[j][0]
					pi_j_y = pi[j][1]

					if var_i == 's' and var_j == 'r':
						if (tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y) in detection_prob:
							lhs = lhs + detection_prob[tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y] * value_of_s[pi_i_x,pi_i_y]

					if var_i == 'r' and var_j == 's':
						if (tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y) in detection_prob:
							lhs = lhs + detection_prob[tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y] * value_of_r[pi_i_x,pi_i_y]

			if instance.CC == 0: # probabilistic model
				if instance.GOAL == 0: # goal: cover all pixels
					if lhs <= log(1-instance.dp): # no cut found
						continue
				else: # goal: deploy equipment
					if lhs <= value_of_c[tx,ty] * log(1-instance.dp): # no cut found
						continue
			else: # cookie-cutter model
				if instance.GOAL == 0: # goal: cover all pixels
					if lhs >= 1.0: # no cut found
						continue
				else: # goal: deploy equipment
					if lhs >= value_of_c[tx,ty]: # no cut found
						continue

			# generate cut

			thevars = []
			thecoefs = []

			if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
				thevars.append(c[tx,ty])
				if instance.CC == 0: # probabilistic model
					thecoefs.append(-log(1-instance.dp))
				else: # cookie-cutter model
					thecoefs.append(-1.0)

			for i in range(2,n+1):
				coef = 0
				var_i = pi[i][2]
				pi_i_x = pi[i][0]
				pi_i_y = pi[i][1]

				for j in range(1,i):
					var_j = pi[j][2]
					pi_j_x = pi[j][0]
					pi_j_y = pi[j][1]

					if var_i == 's' and var_j == 'r':
						if (tx,ty,theta,pi_i_x,pi_i_y,pi_j_x,pi_j_y) in detection_prob:
							coef = coef + detection_prob[tx,ty,theta,pi_i_x,pi_i_y,pi_j_x,pi_j_y]

					if var_i == 'r' and var_j == 's':
						if (tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y) in detection_prob:
							coef = coef + detection_prob[tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y]

				if var_i == 's':
					thevars.append(s[pi_i_x,pi_i_y])
				if var_i == 'r':
					thevars.append(r[pi_i_x,pi_i_y])

				thecoefs.append(coef);

			if instance.CC == 0: # probabilistic model
				if instance.GOAL == 0: # goal: cover all pixels
					self.add(constraint = cplex.SparsePair(thevars,thecoefs), sense = "L", rhs = log(1-instance.dp))
				else: # goal: deploy equipment
					self.add(constraint = cplex.SparsePair(thevars,thecoefs), sense = "L", rhs = 0.0)
			else: # cookie-cutter model
				if instance.GOAL == 0: # goal: cover all pixels
					self.add(constraint = cplex.SparsePair(thevars,thecoefs), sense = "G", rhs = 1.0)
				else: # goal: deploy equipment
					self.add(constraint = cplex.SparsePair(thevars,thecoefs), sense = "G", rhs = 0.0)

			self.number_of_cuts_added += 1

# ---------------------------------------------------
# --- User Cut Callback (for Rodrigues et al., 2014)
# ---------------------------------------------------

class UsercutCallback(UserCutCallback):

	def __call__(self, instance, ocean, detection_prob, s, r, c, theta):
		self.number_of_calls += 1

		# get incumbent solution values

		value_of_s = {}
		value_of_r = {}

		for gx,gy in ocean:
			value_of_s[gx,gy] = self.get_values(s[gx,gy])
			value_of_r[gx,gy] = self.get_values(r[gx,gy])

		if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
			value_of_c = {}
			for tx,ty in ocean:
				value_of_c[tx,ty] = self.get_values(c[tx,ty])

		# sorting

		sort_me = []

		for gx,gy in ocean:
			sort_me.append((gx,gy,'s',value_of_s[gx,gy]))
			sort_me.append((gx,gy,'r',value_of_r[gx,gy]))

		sort_me = sorted(sort_me, key=lambda sort_me: sort_me[3], reverse=True)
		n = len(sort_me)

		# compute permutation

		pi = [(0,0,0,0)]

		for i in range(1,n+1):
			pi.append((sort_me[i-1][0],sort_me[i-1][1],sort_me[i-1][2]))

		for tx,ty in ocean:
			# compute cut strength

			lhs = 0

			for i in range(2,n+1):
				var_i = pi[i][2]
				pi_i_x = pi[i][0]
				pi_i_y = pi[i][1]

				for j in range(1,i):
					var_j = pi[j][2]
					pi_j_x = pi[j][0]
					pi_j_y = pi[j][1]

					if var_i == 's' and var_j == 'r':
						if (tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y) in detection_prob:
							lhs = lhs + detection_prob[tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y] * value_of_s[pi_i_x,pi_i_y]

					if var_i == 'r' and var_j == 's':
						if (tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y) in detection_prob:
							lhs = lhs + detection_prob[tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y] * value_of_r[pi_i_x,pi_i_y]

			if instance.CC == 0: # probabilistic model
				if instance.GOAL == 0: # goal: cover all pixels
					if lhs <= log(1-instance.dp) + instance.USERCUTSTRENGTH: # no cut found
						continue
				else: # goal: deploy equipment
					if lhs <= value_of_c[tx,ty] * log(1-instance.dp) + instance.USERCUTSTRENGTH: # no cut found
						continue
			else: # cookie-cutter model
				if instance.GOAL == 0: # goal: cover all pixels
					if lhs >= 1.0 - instance.USERCUTSTRENGTH: # no cut found
						continue
				else: # goal: deploy equipment
					if lhs >= value_of_c[tx,ty] - instance.USERCUTSTRENGTH: # no cut found
						continue

			# generate cut

			thevars = []
			thecoefs = []

			if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
				thevars.append(c[tx,ty])
				if instance.CC == 0: # probabilistic model
					thecoefs.append(-log(1-instance.dp))
				else: # cookie-cutter model
					thecoefs.append(-1.0)

			for i in range(2,n+1):
				coef = 0
				var_i = pi[i][2]
				pi_i_x = pi[i][0]
				pi_i_y = pi[i][1]

				for j in range(1,i):
					var_j = pi[j][2]
					pi_j_x = pi[j][0]
					pi_j_y = pi[j][1]

					if var_i == 's' and var_j == 'r':
						if (tx,ty,theta,pi_i_x,pi_i_y,pi_j_x,pi_j_y) in detection_prob:
							coef = coef + detection_prob[tx,ty,theta,pi_i_x,pi_i_y,pi_j_x,pi_j_y]

					if var_i == 'r' and var_j == 's':
						if (tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y) in detection_prob:
							coef = coef + detection_prob[tx,ty,theta,pi_j_x,pi_j_y,pi_i_x,pi_i_y]

				if var_i == 's':
					thevars.append(s[pi_i_x,pi_i_y])
				if var_i == 'r':
					thevars.append(r[pi_i_x,pi_i_y])

				thecoefs.append(coef);

			if instance.CC == 0: # probabilistic model
				if instance.GOAL == 0: # goal: cover all pixels
					self.add(cut = cplex.SparsePair(thevars,thecoefs), sense = "L", rhs = log(1-instance.dp))
				else: # goal: deploy equipment
					self.add(cut = cplex.SparsePair(thevars,thecoefs), sense = "L", rhs = 0.0)
			else: # cookie-cutter model
				if instance.GOAL == 0: # goal: cover all pixels
					self.add(cut = cplex.SparsePair(thevars,thecoefs), sense = "G", rhs = 1.0)
				else: # goal: deploy equipment
					self.add(cut = cplex.SparsePair(thevars,thecoefs), sense = "G", rhs = 0.0)

			self.number_of_cuts_added += 1
