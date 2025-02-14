DIR        = "data/"  # directory where to find input and store output files
INPUT      = "Iceland_20250214_120117.asc"            # file name of ocean floor data
RAM        = 131072                     # RAM allocation in MB
X          = 10                         # number of pixels in x-direction
Y          = 10                         # number of pixels in y-direction
GOAL       = 1                          # optimization goal: cover all pixels, minimize cost (0), or maximize coverage (1)

# Equipment parameters
S          = 4                    # number of deployed sources
R          = 12                    # number of deployed receivers

# Physical parameters
RHO_0      = 8000                # range of the day (in yards)
RB         = 750                 # pulse length (for direct-blast-effect) (in yards)
FREQ       = 8000                # frequency of the sonar (in Hz)

# Depth configuration
RX_DEPTHS  = [90, 200, 400, 1000]
TX_DEPTHS  = [50, 150, 300, 90, 400, 1500]

# Target strength configuration
TS         = [(0.0,2000),(10.0,0),(20.0,2000),(30.0,3000),(40.0,4000),(50.0,2000),(60.0,4000),(70.0,6000),(80.0,6000),(90.0,10000),(100.0,8000),(110.0,6000),(120.0,0),(130.0,2000),(140.0,4000),(150.0,-3000),(160.0,-2000),(170.0,-2500),(180.0,2000)]          # target strength function

# Optimization parameters
STEPS               = 30         # step size for discretization of half-circle
BOUND               = 1          # 0=individual bound per row, 1=min/max over all rows
USERCUTS            = 0          # 0=no user cuts, 1=user cuts on
USERCUTSTRENGTH     = 1.0        # how deep must user cuts be to be separated?
HEURISTIC           = 50       # 0=no heuristic, >0: with heuristic, number of rounds
SOLVE               = 2          # 0=only root relaxation, 1=root+cuts, 2=to the end
TIMELIMIT           = 86400      # time limit in seconds
TIMELIMIT_HEURISTIC = 1728        # time limit in seconds