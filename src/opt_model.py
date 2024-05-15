import random
import time

import cplex
from cplex.exceptions import CplexSolverError

from src.functions import *
from src.classes import *

def opt_model(instance, ocean, detection_prob, detection_prob_rowsum_s, outdir):

	model = cplex.Cplex()

	print ("IBM ILOG CPLEX version number: ", model.get_version())

	# VARIABLES

	s = {} # sources, =1, if a source is located on candidate location gx,gy
	r = {} # receivers, =1, if a receiver is located on candidate location gx,gy

	for gx,gy in ocean:
		s[gx,gy] = "s#"+str(gx)+"#"+str(gy)
		r[gx,gy] = "r#"+str(gx)+"#"+str(gy)

		if instance.GOAL == 0: # optimization goal: cover all pixels, minimize deployment cost
			model.variables.add(obj = [instance.S], names = [s[gx,gy]], lb = [0], ub = [1], types = ["B"])
			model.variables.add(obj = [instance.R], names = [r[gx,gy]], lb = [0], ub = [1], types = ["B"])
		else: # deploy equipment, maximize coverage
			model.variables.add(names = [s[gx,gy]], lb = [0], ub = [1], types = ["B"])
			model.variables.add(names = [r[gx,gy]], lb = [0], ub = [1], types = ["B"])

	if instance.GOAL == 1: # deploy equipment, maximize coverage
		c = {} # coverage, =1, if some source-receiver pair covers location tx,ty

		percentage = float("{0:.3f}".format(100.0/len(ocean)))

		for tx,ty in ocean:
			c[tx,ty] = "c#"+str(tx)+"#"+str(ty)
			model.variables.add(obj = [percentage], names = [c[tx,ty]], lb = [0], ub = [1], types = ["B"])

	if instance.MODELTYPE in {4,5,7,8,10,11,13,14}:
		y = {}

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			y[tx,ty,theta,gx,gy] = "y#"+str(tx)+"#"+str(ty)+"#"+str(theta)+"#"+str(gx)+"#"+str(gy)

			if instance.CC == 0: # probabilistic model
				model.variables.add(names = [y[tx,ty,theta,gx,gy]], lb = [detection_prob_rowsum_s[tx,ty,theta,gx,gy]], ub = [0], types = ["C"])
			else: # cookie-cutter model
				model.variables.add(names = [y[tx,ty,theta,gx,gy]], ub = [detection_prob_rowsum_s[tx,ty,theta,gx,gy]], lb = [0], types = ["C"])

				# TODO: Setting y to general integer seems to help for cookie-cutter. Perform a deeper analysis of this initial observation
				#model.variables.add(names = [y[tx,ty,theta,gx,gy]], ub = [detection_prob_rowsum_s[tx,ty,theta,gx,gy]], lb = [0], types = ["I"])

	# CONSTRAINTS

	# probabilistic models

	if instance.GOAL == 1:
		# for all models below, if the goal is to 'deploy equipment, maximize coverage', then here the equipment gets fixed

		thevars = []
		thecoefs = []

		for gx,gy in ocean:
			thevars.append(s[gx,gy])
			thecoefs.append(1.0)

		model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [instance.S])

		thevars = []
		thecoefs = []

		for g1x,g1y in ocean:
			thevars.append(r[g1x,g1y])
			thecoefs.append(1.0)

		model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [instance.R])

	else: # GOAL = 0
		# for all models below, if the goal is to 'minimize equipment', then at least one source and one receiver have to be deployed

		thevars = []
		thecoefs = []

		for gx,gy in ocean:
			thevars.append(s[gx,gy])
			thecoefs.append(1.0)

		model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])

		thevars = []
		thecoefs = []

		for g1x,g1y in ocean:
			thevars.append(r[g1x,g1y])
			thecoefs.append(1.0)

		model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])

	if instance.MODELTYPE == 7:
		# 1st linearization from Oral, Kettani (1992) for senders

		# coverage for each ocean pixel

		for tx,ty in ocean:
			for theta in range(0,180,instance.STEPS): # target angle
				thevars = []
				thecoefs = []

				for gx,gy in ocean:
					thevars.append(s[gx,gy])
					thevars.append(y[tx,ty,theta,gx,gy])
					thecoefs.append(detection_prob_rowsum_s[tx,ty,theta,gx,gy])
					thecoefs.append(-1.0)

				if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
					thevars.append(c[tx,ty])
					if instance.CC == 0: # probabilistic model
						thecoefs.append(-log(1-instance.dp))
					else: # cookie-cutter model
						thecoefs.append(-1.0)

				if instance.CC == 0: # probabilistic model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [log(1-instance.dp)])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
				else: # cookie-cutter model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

		# linearization constraints

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			thevars = [y[tx,ty,theta,gx,gy],s[gx,gy]]
			thecoefs = [1.0,-detection_prob_rowsum_s[tx,ty,theta,gx,gy]]

			for g1x,g1y in ocean:
				if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
					thevars.append(r[g1x,g1y])
					thecoefs.append(detection_prob[tx,ty,theta,gx,gy,g1x,g1y])

			if instance.CC == 0: # probabilistic model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
			else: # cookie-cutter model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

	if instance.MODELTYPE == 10:
		# 2nd linearization from Oral, Kettani (1992) for sources

		# coverage for each ocean pixel

		for tx,ty in ocean:
			for theta in range(0,180,instance.STEPS): # target angle
				thevars = []
				thecoefs = []

				for gx,gy in ocean:
					thevars.append(y[tx,ty,theta,gx,gy])
					thecoefs.append(-1.0)

				for g1x,g1y in ocean:
					sum = 0
					for gx,gy in ocean:
						if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
							sum = sum + detection_prob[tx,ty,theta,gx,gy,g1x,g1y]

					thevars.append(r[g1x,g1y])
					thecoefs.append(sum)

				if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
					thevars.append(c[tx,ty])
					if instance.CC == 0: # probabilistic model
						thecoefs.append(-log(1-instance.dp))
					else: # cookie-cutter model
						thecoefs.append(-1.0)

				if instance.CC == 0: # probabilistic model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [log(1-instance.dp)])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
				else: # cookie-cutter model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

		# linearization constraints

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			thevars = [y[tx,ty,theta,gx,gy],s[gx,gy]]
			thecoefs = [-1.0,-detection_prob_rowsum_s[tx,ty,theta,gx,gy]]

			for g1x,g1y in ocean:
				if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
					thevars.append(r[g1x,g1y])
					thecoefs.append(detection_prob[tx,ty,theta,gx,gy,g1x,g1y])

			if instance.CC == 0: # probabilistic model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])
			else: # cookie-cutter model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])

	if instance.MODELTYPE == 13:
		# linearization from Chaovalitwongse, Pardalos, Prokopyev (2004) for sources

		# coverage for each ocean pixel

		for tx,ty in ocean:
			for theta in range(0,180,instance.STEPS): # target angle
				thevars = []
				thecoefs = []

				for gx,gy in ocean:
					thevars.append(y[tx,ty,theta,gx,gy])
					thecoefs.append(1.0)

				if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
					thevars.append(c[tx,ty])
					if instance.CC == 0: # probabilistic model
						thecoefs.append(-log(1-instance.dp))
					else: # cookie-cutter model
						thecoefs.append(-1.0)

				if instance.CC == 0: # probabilistic model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [log(1-instance.dp)])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
				else: # cookie-cutter model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

		# linearization constraints

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			thevars = [y[tx,ty,theta,gx,gy],s[gx,gy]]
			thecoefs = [-1.0,detection_prob_rowsum_s[tx,ty,theta,gx,gy]]

			if instance.CC == 0: # probabilistic model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
			else: # cookie-cutter model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			thevars = [y[tx,ty,theta,gx,gy]]
			thecoefs = [-1.0]

			for g1x,g1y in ocean:
				if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
					thevars.append(r[g1x,g1y])
					thecoefs.append(detection_prob[tx,ty,theta,gx,gy,g1x,g1y])

			if instance.CC == 0: # probabilistic model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
			else: # cookie-cutter model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

	if instance.USERCUTS == 1:
		usercut_cb = model.register_callback(UsercutCallback)
		usercut_cb.number_of_calls = 0
		usercut_cb.number_of_cuts_added = 0

	# OBJECTIVE FUNCTION

	if instance.GOAL == 0: # goal: minimize cost for deployed equipment
		model.objective.set_sense(model.objective.sense.minimize)
	else: # goal: maximize coverage
		model.objective.set_sense(model.objective.sense.maximize)

	# set optimization parameters

	#model.parameters.threads.set(1);   # single core, no parallelism

	# HEURISTIC

	if instance.HEURISTIC > 0:
		print ("running",instance.HEURISTIC,"rounds of heuristic")

		model.set_results_stream(None) # turn off messaging to screen
		model.set_warning_stream(None)

		if instance.GOAL == 0:
			best_obj = 10**10

			best_sources = []
			best_receivers = []

			#print ("----------",0,"-----------")

			# PREQUEL

			fixed_receivers = ocean

			old_obj = 10**10

			while True:

				# fix the receiver variables of the positions in fixed_receivers to 1, and all others to 0
				# free the sources

				for (rx,ry) in ocean:
					if (rx,ry) in fixed_receivers:
						model.variables.set_lower_bounds(r[rx,ry],1)
						model.variables.set_upper_bounds(r[rx,ry],1)
					else:
						model.variables.set_lower_bounds(r[rx,ry],0)
						model.variables.set_upper_bounds(r[rx,ry],0)

				for (sx,sy) in ocean:
					model.variables.set_lower_bounds(s[sx,sy],0)
					model.variables.set_upper_bounds(s[sx,sy],1)

				#model.write(outdir+"/bison.lp")

				# get positions of sources

				model.solve()

				obj = model.solution.get_objective_value()
				#print ("Solution value = ",obj)

				fixed_sources = {}

				for (sx,sy) in ocean:
					if model.solution.get_values(s[sx,sy]) > 0.999:
						#print ("got one source at ",sx,sy)
						fixed_sources[sx,sy] = 1

				# fix the source variables of the positions in fixed_sources to 1, and all others to 0
				# free the receiver variables again

				for (sx,sy) in ocean:
					if (sx,sy) in fixed_sources:
						model.variables.set_lower_bounds(s[sx,sy],1)
						model.variables.set_upper_bounds(s[sx,sy],1)
					else:
						model.variables.set_lower_bounds(s[sx,sy],0)
						model.variables.set_upper_bounds(s[sx,sy],0)

				for (rx,ry) in ocean:
					model.variables.set_lower_bounds(r[rx,ry],0)
					model.variables.set_upper_bounds(r[rx,ry],1)

				# get positions of sources

				model.solve()

				obj = model.solution.get_objective_value()
				#print ("Solution value = ",obj)

				fixed_receivers = {}
				for (rx,ry) in ocean:
					if model.solution.get_values(r[rx,ry]) > 0.999:
						#print ("got one receiver at ",rx,ry)
						fixed_receivers[rx,ry] = 1

				# LOOP
				if (old_obj > obj):
					old_obj = obj
				else:
					break

			best_receivers = fixed_receivers
			best_sources = fixed_sources
			best_obj = obj

			number_of_sources = len(fixed_sources)
			number_of_receivers = len(fixed_receivers)

			print ("  found new incumbent at iteration 0 with objective value",obj)

			# number of sources fixed in the model

			thevars = []
			thecoefs = []

			for gx,gy in ocean:
				thevars.append(s[gx,gy])
				thecoefs.append(1.0)

			model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [number_of_sources])

			# LOOP HEURISTIC

			list_of_fixed_sources = []

			for round in range(instance.HEURISTIC - 1):
				print ("----------",round+1,"-----------")

				# INNER LOOP

				while True:
					fixed_sources = {}

					while len(fixed_sources) < number_of_sources:
						sx,sy = random.choice(list(ocean.keys()))

						if (sx,sy) not in fixed_sources:
							fixed_sources[sx,sy] = 1

					if (fixed_sources not in list_of_fixed_sources):
						list_of_fixed_sources.append(fixed_sources)
						break

					#print ("do it again")

				# fix the source variables of the positions in fixed_sources to 1, and all others to 0
				# free the receivers

				for (sx,sy) in ocean:
					if (sx,sy) in fixed_sources:
						model.variables.set_lower_bounds(s[sx,sy],1)
						model.variables.set_upper_bounds(s[sx,sy],1)
					else:
						model.variables.set_lower_bounds(s[sx,sy],0)
						model.variables.set_upper_bounds(s[sx,sy],0)

				for (rx,ry) in ocean:
					model.variables.set_lower_bounds(r[rx,ry],0)
					model.variables.set_upper_bounds(r[rx,ry],1)

				#model.write(outdir+"/bison.lp")

				# get positions of sources

				model.solve()

				if (model.solution.get_status_string() != 'integer infeasible'):

					obj = model.solution.get_objective_value()
					#print ("Solution value = ",obj)

					fixed_receivers = {}
					for (rx,ry) in ocean:
						if model.solution.get_values(r[rx,ry]) > 0.999:
							#print ("got one receiver at ",rx,ry)
							fixed_receivers[rx,ry] = 1

					if best_obj > obj:
						best_obj = obj
						best_receivers = fixed_receivers
						best_sources = fixed_sources
						print ("  found new incumbent at iteration",round,"with objective value",obj)

		else: # GOAL = 1
			best_obj = -1

			best_sources = []
			best_receivers = []

			list_of_fixed_sources = []

			for round in range(instance.HEURISTIC):
				print ("----------",round,"-----------")
				
				# INNER LOOP

				while True:
					fixed_sources = {}

					while len(fixed_sources) < instance.S:
						sx,sy = random.choice(list(ocean.keys()))

						if (sx,sy) not in fixed_sources:
							fixed_sources[sx,sy] = 1

					if fixed_sources not in list_of_fixed_sources:
						list_of_fixed_sources.append(fixed_sources)
						print ("new:",fixed_sources)
						break

					print ("(do it again)")

				print ("fixing sources at:",fixed_sources)

				old_obj = -1

				while True:

					# fix the source variables of the positions in fixed_sources to 1, and all others to 0
					# free the receivers

					for (sx,sy) in ocean:
						if (sx,sy) in fixed_sources:
							model.variables.set_lower_bounds(s[sx,sy],1)
							model.variables.set_upper_bounds(s[sx,sy],1)
						else:
							model.variables.set_lower_bounds(s[sx,sy],0)
							model.variables.set_upper_bounds(s[sx,sy],0)

					for (rx,ry) in ocean:
						model.variables.set_lower_bounds(r[rx,ry],0)
						model.variables.set_upper_bounds(r[rx,ry],1)

					#model.write(outdir+"/bison.lp")

					# get positions of receivers

					model.solve()

					print ("Solution value (ocean coverage percentage) = ", model.solution.get_objective_value())

					fixed_receivers = {}
					for (rx,ry) in ocean:
						if model.solution.get_values(r[rx,ry]) > 0.999:
							#print ("got one receiver at ",rx,ry)
							fixed_receivers[rx,ry] = 1

					# fix the receiver variables of the positions in fixed_receivers to 1, and all others to 0
					# free the source variables again

					for (rx,ry) in ocean:
						if (rx,ry) in fixed_receivers:
							model.variables.set_lower_bounds(r[rx,ry],1)
							model.variables.set_upper_bounds(r[rx,ry],1)
						else:
							model.variables.set_lower_bounds(r[rx,ry],0)
							model.variables.set_upper_bounds(r[rx,ry],0)

					for (sx,sy) in ocean:
						model.variables.set_lower_bounds(s[sx,sy],0)
						model.variables.set_upper_bounds(s[sx,sy],1)

					# get positions of sources

					model.solve()

					obj = model.solution.get_objective_value()
					print ("Solution value (ocean coverage percentage) = ", obj)

					fixed_sources = {}
					for (sx,sy) in ocean:
						if model.solution.get_values(s[sx,sy]) > 0.999:
							#print ("got one source at ",sx,sy)
							fixed_sources[sx,sy] = 1

					# LOOP
					if (old_obj < obj):
						old_obj = obj
					else:
						break


				if best_obj < obj:
					best_obj = obj
					best_receivers = fixed_receivers
					best_sources = fixed_sources
					print ("  found new incumbent at iteration",round,"with objective value",obj)

		# resort to best solution (as MIP starter)

		#print ("best objective ",best_obj)
		#print ("best receivers ",best_receivers)
		#print ("best sources ",best_sources)

		for (rx,ry) in ocean:
			if (rx,ry) in best_receivers:
				model.variables.set_lower_bounds(r[rx,ry],1)
				model.variables.set_upper_bounds(r[rx,ry],1)
			else:
				model.variables.set_lower_bounds(r[rx,ry],0)
				model.variables.set_upper_bounds(r[rx,ry],0)

		for (sx,sy) in ocean:
					if (sx,sy) in best_sources:
						model.variables.set_lower_bounds(s[sx,sy],1)
						model.variables.set_upper_bounds(s[sx,sy],1)
					else:
						model.variables.set_lower_bounds(s[sx,sy],0)
						model.variables.set_upper_bounds(s[sx,sy],0)

		#model.write(outdir+"/bison.lp")
		model.solve()

		# free everything

		for (sx,sy) in ocean:
					model.variables.set_lower_bounds(s[sx,sy],0)
					model.variables.set_upper_bounds(s[sx,sy],1)

		for (rx,ry) in ocean:
					model.variables.set_lower_bounds(r[rx,ry],0)
					model.variables.set_upper_bounds(r[rx,ry],1)

		# turn on messaging to screen

		model.set_results_stream(sys.stdout)
		model.set_warning_stream(sys.stdout)


	# write model

	model.write(outdir + "/bison.lp")

	# solve model

	if instance.SOLVE == 0: # solve root relaxation (without cuts)
		model.set_problem_type(type=model.problem_type.LP)

		try:
			start = time.time()
			model.solve()
			end = time.time()
			print ("it took","{0:.2f}".format(end - start),"sec to solve root")

		except (CplexSolverError) as exc:
			print ("** Exception: ",exc)

		solution = model.solution
		print ("Solution value = ", solution.get_objective_value())
		quit()

	if instance.SOLVE == 1: # solve roots+cuts
		model.parameters.mip.limits.nodes.set(0)

		try:
			start = time.time()
			model.solve()
			end = time.time()
			print ("it took","{0:.2f}".format(end - start),"sec to solve root+cuts")

		except (CplexSolverError) as exc:
			print ("** Exception: ",exc)

		solution = model.solution
		print ("Solution value = ", solution.get_objective_value())
		print ("Best bound = ", solution.MIP.get_best_objective())
		quit()

	# solve to optimality (0.0%), until timelimit reached

	model.parameters.timelimit.set(instance.TIMELIMIT)
	model.parameters.mip.tolerances.mipgap.set(0.0)
	model.parameters.workmem.set(instance.RAM)                      # set workmem to 8 GByte
	model.parameters.mip.strategy.file.set(2)               # store node file on disk (uncompressed) when workmem is exceeded

	try:
		start = time.time()
		model.solve()
		end = time.time()
		print ("it took","{0:.2f}".format(end - start),"sec to solve")

	except (CplexSolverError) as exc:
		print ("** Exception: ",exc)

	# solution interpretation

	solution = model.solution