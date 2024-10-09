DIR = "Instances/OpenSeaBiscaya/" # directory where to find input and store output files
INPUT = "GMRTv3_3_20170615topo.asc" # file name of ocean floor data

RAM =2*8192	# 0=use disk, 1=use RAM for storing data

X = 10 # number of pixels in x-direction
Y = 10 # number of pixels in y-direction

GOAL = 1 # optimization goal: cover all pixels, minimize cost for deployed equipment (0) or deploy equipment, maximize coverage (1)

S = 3 # EITHER: cost for each deployed source (if GOAL=0), OR: number of deployed sources (if GOAL=1)
R = 12 # EITHER: cost for each deployed receiver (if GOAL=0), OR: number of deployed receivers (if GOAL=1)

rho_0 = 2 # range of the day (in pixels)
rb = 1 # pulse length (for direct-blast-effect) (in pixels)

dp = 0.95 # desired minimum detection probability per area; only relevant for probabilistic model
pmax = 0.95 # maximum detection probability for single sender/receiver pair (remark: never set probability to 1, because of taking the log); only relevant for probabilistic model
pmin = 0.1 # minimum detection probability for single sender/receiver pair; only relevant for probabilistic model
b1 = 0.2 # parameter to describe how fast the detection probability decays at the outer (range) boundary; only relevant for probabilistic model
b2 = 0.1 # parameter to describe how fast the detection probability decays at the inner (direct blast) boundary; only relevant for probabilistic model

#TS = [(0.0,0.1),(30.0,0.4),(75.0,0.3),(90.0,1.0)] # target strength (in pixels), added to the range of the day, 0 (degree) = bow/stern, 90 (degree) = beam 
TS = [] # if TS is an empty list, the target angle is not considered
STEPS = 30 # step size for discretization of half-circle (eg., "10" degrees gives 0,10,20,...,170)

BOUND = 1 # 0=individual bound per row, 1=min/max over all rows

USERCUTS = 0 # 0=no user cuts, 1=user cuts on

USERCUTSTRENGTH = 1.0 # how deep must user cuts be to be separated?

HEURISTIC = 100 # 0=no heuristic, >0: with heuristic, number of rounds

SOLVE = 2 # 0=only root relaxation, 1=root+cuts, 2=to the end (optimality or timelimit reached)

TIMELIMIT = 3600 # time limit in seconds
