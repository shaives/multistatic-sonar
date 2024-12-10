DIR = "Instances/MontereyPeninsular/" # directory where to find input and store output files
INPUT = "GMRTv3_3_20170309topo.asc" # file name of ocean floor data

RAM = 16*8192	# 0=use disk, 1=use RAM for storing data

X = 10 # number of pixels in x-direction maybe dynamic for max 1.3 range of the day
Y = 10 # number of pixels in y-direction

GOAL = 0 # optimization goal: cover all pixels, minimize cost for deployed equipment (0) or deploy equipment, maximize coverage (1)

S = 12000 # EITHER: cost for each deployed source (if GOAL=0), OR: number of deployed sources (if GOAL=1)
R = 800 # EITHER: cost for each deployed receiver (if GOAL=0), OR: number of deployed receivers (if GOAL=1)

S_DEPTH = {'tx_d1' : 90, 'tx_d2' : 200, 'tx_d3' : 400 , 'tx_d4' : 1000} # depth of source (in feet)
R_DEPTH = {'rx_d1_1' : 50, 'rx_d1_2' : 150, 'rx_d1_3' : 300, 'rx_d2_1' : 90, 'rx_d2_2' : 400, 'rx_d2_1' : 1500} # depth of receiver (in feet)

rho_0 = 8000 # range of the day (in yards)
rb = 750 # pulse length cw 0.5s (for direct-blast-effect) (in yards)

TS = [(0.0,0.1),(30.0,0.4),(75.0,0.3),(90.0,1.0)] # target strength (in pixels), added to the range of the day, 0 (degree) = bow/stern, 90 (degree) = beam 
#TS = [] # if TS is an empty list, the target angle is not considered
STEPS = 30 # step size for discretization of half-circle (eg., "10" degrees gives 0,10,20,...,170)

BOUND = 1 # 0=individual bound per row, 1=min/max over all rows

USERCUTS = 0 # 0=no user cuts, 1=user cuts on

USERCUTSTRENGTH = 1.0 # how deep must user cuts be to be separated?

HEURISTIC = 200 # 0=no heuristic, >0: with heuristic, number of rounds

SOLVE = 2 # 0=only root relaxation, 1=root+cuts, 2=to the end (optimality or timelimit reached)

TIMELIMIT_HEURISTIC = 1800 # time limit in seconds
TIMELIMIT = 36000 # time limit in seconds
