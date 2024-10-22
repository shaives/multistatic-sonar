# multistatic-sonar

bison.py runs with python3

Requires libraries: NumPy, MatPlotLib, IBM ILOG Cplex

IBM ILOG Cplex can be obtained via IBM Academic Initiative for free.

Call: python3 bison.py `<instance name>`

`<instance name>` is one of the 30 instances provided. For example:

python3 bison.py Agadir

The file Agadir.py contains further settings for the solver.

bisonranch.pl is a Perl script that calls bison.py for a bunch of instances, so that a table with computational results can be generated with one function call. It runs for several weeks...
