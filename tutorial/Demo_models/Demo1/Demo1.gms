$TITLE    Demo1.gms

* version: no time-step

 option limrow=10000;
 option limcol=10000;

** ----------------------------------------------------------------------
**  Loading Data: sets, parameters and tables
** ----------------------------------------------------------------------

$        include "dataset 1.txt";

** ----------------------------------------------------------------------
**  Model variables and equations
** ----------------------------------------------------------------------

VARIABLES
Q(i,j) flow in each link in each period
delivery (i) water delivered to demand node i in each period
Z objective function
;

POSITIVE VARIABLES
Q
;

EQUATIONS
MassBalance_nonstorage(ns_nodes)
MinFlow(i,j)
MaxFlow(i,j)
Demand(dem_nodes)
Objective
;

* Objective function

Objective ..
    Z =E= SUM((i,j)$links(i,j), Q(i,j) * cost(i,j))
;

*Calculating water delivery for each demand node at each time step

Demand(dem_nodes)..
         delivery(dem_nodes) =E= SUM(j$links(j,dem_nodes), flowmultiplier(j,dem_nodes)
         *Q(j,dem_nodes));

* Mass balance constrait for non-storage nodes

MassBalance_nonstorage(ns_nodes) ..
    inflow(ns_nodes)+
    SUM(j$links(j,ns_nodes), Q(j,ns_nodes)* flowmultiplier(j,ns_nodes))
    - SUM(j$links(ns_nodes,j), Q(ns_nodes,j))
    - cc(ns_nodes)$dem_nodes(ns_nodes) * delivery(ns_nodes)
    =E= 0;

* Lower and upper bound of possible flow in links

MinFlow(i,j)$links(i,j) ..
    Q(i,j) =G= lower(i,j);

MaxFlow(i,j)$links(i,j) ..
    Q(i,j) =L= upper(i,j);

** ----------------------------------------------------------------------
**  Model declaration and solve statements
** ----------------------------------------------------------------------

MODEL Demo1 /ALL/;

SOLVE Demo1 USING LP MINIMIZING Z;

*Generating results output

execute_unload "Results.gdx" ,
    Q,
    MassBalance_nonstorage,
    MinFlow,
    MaxFlow,
    Z
    cost;