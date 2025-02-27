# multistatic-sonar

Python Version 3.10.10

Requires libraries see requirements.in

CPLEX Version 22.1.2.0 or Gurobi

IBM ILOG Cplex can be obtained via IBM Academic Initiative for free.
Gurobi Optimization, LLC, Gurobi can be obtained via Academic Initiative for free.

Other solvers should also work with the Pyomo as long as you add them in the optimization.py 

Call: python3 bison.py `<instance name>`

`<instance name>` is one of the 10 instances provided. 

For example:

python3 bison.py Iceland_cost

The file Iceland_cost.py contains further settings for the solver.

If you want to run it on an HPC you can use the shell files. 

Define the `<instance name>` inside shell before you run it.

For Example:

sbatch drop.sh

drop.sh     -> a single instnace will be run
node.sh     -> a single instnace will be run on the node you set
ranch.sh    -> runs as many instaces as you define parallel


