$TITLE    Demo.gms
* v time-step by time-step

** ----------------------------------------------------------------------
**  Loading Data: sets, parameters and tables
** ----------------------------------------------------------------------

$        include "Input.txt";

** ----------------------------------------------------------------------
**  Model variables and equations
** ----------------------------------------------------------------------

VARIABLES
Q(i,j,t) flow in each link in each period
S(i,t) storage volume in storage nodes
delivery (i,t) water delivered to demand node i in each period
Z objective function
;

POSITIVE VARIABLES
Q
S
;

EQUATIONS
MassBalance_nonstorage(mb_ns_nodes,t)
MassBalance_storage(mb_s_nodes,t)
MinFlow(i,j,t)
MaxFlow(i,j,t)
MaxStor(mb_s_nodes,t)
MinStor(mb_s_nodes,t)
Demand(dem_nodes,t)
Objective
;

* Objective function for time step by time step formulation

Objective ..
    Z =E= SUM(t,SUM((i,j)$links(i,j), Q(i,j,t) * cost(i,j,t)));

*Calculating water delivery for each demand node at each time step

Demand(dem_nodes,t)..
         delivery(dem_nodes,t) =E= SUM(j$links(j,dem_nodes), Q(j,dem_nodes,t));

* Mass balance constrait for non-storage nodes

MassBalance_nonstorage(mb_ns_nodes,t) ..
    SUM(j$links(j,mb_ns_nodes), Q(j,mb_ns_nodes,t))
    - SUM(j$links(mb_ns_nodes,j), Q(mb_ns_nodes,j,t)* flowmultiplier(mb_ns_nodes,j,t))
    - cc(mb_ns_nodes)$dem_nodes(mb_ns_nodes) * delivery(mb_ns_nodes,t)
    =E= 0;

* Storage constraint for storage nodes:

MassBalance_storage(mb_s_nodes,t)..

         SUM(j$links(j,mb_s_nodes), Q(j,mb_s_nodes,t))
         - SUM(j$links(mb_s_nodes,j), Q(mb_s_nodes,j,t) * flowmultiplier(mb_s_nodes,j,t) )
         -S(mb_s_nodes,t)
         +S(mb_s_nodes,t--1)$(ord(t) GT 1)
         + initStor(mb_s_nodes,t)$(ord(t) EQ 1)
         =E= 0;

* Lower and upper bound of possible flow in links

MinFlow(i,j,t)$links(i,j) ..
    Q(i,j,t) =G= lower(i,j,t);

MaxFlow(i,j,t)$links(i,j) ..
    Q(i,j,t) =L= upper(i,j,t);

* Lower and upper bound of Storage volume at storage nodes
MaxStor(mb_s_nodes,t)..
    S(mb_s_nodes,t) =L= storageupper(mb_s_nodes,t);

MinStor(mb_s_nodes,t)..
    S(mb_s_nodes,t) =G= storagelower(mb_s_nodes,t);

** ----------------------------------------------------------------------
**  Model declaration and solve statements
** ----------------------------------------------------------------------

MODEL Demo /ALL/;

SOLVE Demo USING LP MINIMIZING Z;

execute_unload "Results.gdx" ,
    Q,
    S,
    MassBalance_storage,
    MassBalance_nonstorage,
    Z
