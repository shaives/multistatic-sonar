
DIR = "Instances/WonsanBay/" # directory where to find input and store output files

INPUT = "GMRTv3_3_20170611topo.asc" # file name of ocean floor data
OUTPUT = "WonsanBay" # name of output file (a time stamp will be added in front of this)

X = 15 # number of pixels in x-direction
Y = 14 # number of pixels in y-direction

GOAL = 1 # optimization goal: cover all pixels, minimize cost for deployed equipment (0) or deploy equipment, maximize coverage (1)

S = 2 # EITHER: cost for each deployed source (if GOAL=0), OR: number of deployed sources (if GOAL=1)
R = 2 # EITHER: cost for each deployed receiver (if GOAL=0), OR: number of deployed receivers (if GOAL=1)

rho_0 = 4 # range of the day (in pixels)
rb = 0.4 # pulse length (for direct-blast-effect) (in pixels)

CC = 1 # cookie cutter model (1), or probabilistic model (0)

dp = 0.95 # desired minimum detection probability per area; only relevant for probabilistic model
pmax = 0.95 # maximum detection probability for single sender/receiver pair (remark: never set probability to 1, because of taking the log); only relevant for probabilistic model
pmin = 0.1 # minimum detection probability for single sender/receiver pair; only relevant for probabilistic model
b1 = 0.2 # parameter to describe how fast the detection probability decays at the outer (range) boundary; only relevant for probabilistic model
b2 = 0.1 # parameter to describe how fast the detection probability decays at the inner (direct blast) boundary; only relevant for probabilistic model
BOUND = 0 # for models 3-14: 0=individual bound per row, 1=min/max over all rows

USERCUTS = 0 # 0=no user cuts, 1=user cuts on

USERCUTSTRENGTH = 1.0 # how deep must user cuts be to be separated?

MODELTYPE = 13 # select model type: 
  # 0=MINLP/let cplex do the job 
  # 1=Fortet (1959), Dantzig (1960), Balas (1964), Zangwill (1965), Watters (1967) 
  # 2=Glover, Woolsey (1974) 
  # 3=Glover (1975) for receivers
  # 4=Glover (1975) for sources
  # 5=Glover (1975) for sources&receivers 
  # 6=1st Oral-Kettani (1992) for receivers
  # 7=1st Oral-Kettani (1992) for sources 
  # 8=1st Oral-Kettani (1992) for sources&receivers 
  # 9=2nd Oral-Kettani (1992) for receivers
  # 10=2nd Oral-Kettani (1992) for sources
  # 11=2nd Oral-Kettani (1992) for sources&receivers
  # 12=Chaovalitwongse, Pardalos, Prokopyev (2004) for receivers
  # 13=Chaovalitwongse, Pardalos, Prokopyev (2004) for sources
  # 14=Chaovalitwongse, Pardalos, Prokopyev (2004) for sources&receivers
  # 15=Rodrigues et al. (2014) 

SOLVE = 2 # 0=only root relaxation, 1=root+cuts, 2=to the end (optimality or timelimit reached)

TIMELIMIT = 10000 # time limit in seconds
