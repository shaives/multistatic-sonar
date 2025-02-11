DIR = "Instances/MontereyPeninsular/" # directory where to find input and store output files
INPUT = "GMRTv3_3_20170309topo.asc" # file name of ocean floor data

RAM = 16*8192	# 0=use disk, 1=use RAM for storing data

X = 10 # number of pixels in x-direction
Y = 10 # number of pixels in y-direction

GOAL = 1 # optimization goal: cover all pixels, minimize cost for deployed equipment (0) or deploy equipment, maximize coverage (1)

S = 4 # EITHER: cost for each deployed source (if GOAL=0), OR: number of deployed sources (if GOAL=1)
R = 12 # EITHER: cost for each deployed receiver (if GOAL=0), OR: number of deployed receivers (if GOAL=1)

RX_DEPTHS  = [90, 200, 400, 1000]
TX_DEPTHS  = [50, 150, 300, 90, 400, 1500]

rho_0 = 8000 # range of the day (in yards)
rb = 750 # pulse length cw 0.5s (for direct-blast-effect) (in yards)

TS = [(0.0,2000),(10.0,0),(20.0,2000),(30.0,3000),(40.0,4000),(50.0,2000),(60.0,4000),(70.0,6000),(80.0,6000),(90.0,10000),(100.0,8000),(110.0,6000),(120.0,0),(130.0,2000),(140.0,4000),(150.0,-3000),(160.0,-2000),(170.0,-2500),(180.0,2000)] # target strength (in pixels), added to the range of the day, 0 (degree) = bow/stern, 90 (degree) = beam 
#TS = [] # if TS is an empty list, the target angle is not considered
STEPS = 30 # step size for discretization of half-circle (eg., "10" degrees gives 0,10,20,...,170)

BOUND = 1 # 0=individual bound per row, 1=min/max over all rows

USERCUTS = 0 # 0=no user cuts, 1=user cuts on

USERCUTSTRENGTH = 1.0 # how deep must user cuts be to be separated?

HEURISTIC = 50 # 0=no heuristic, >0: with heuristic, number of rounds

SOLVE = 2 # 0=only root relaxation, 1=root+cuts, 2=to the end (optimality or timelimit reached)

TIMELIMIT_HEURISTIC = 1800 # time limit in seconds
TIMELIMIT = 36000 # time limit in seconds
