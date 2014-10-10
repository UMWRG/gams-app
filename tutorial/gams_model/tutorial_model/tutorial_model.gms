$TITLE    Demo.gms
* v time-step by time-step

** ----------------------------------------------------------------------
**  Loading Data: sets, parameters and tables
** ----------------------------------------------------------------------

$        include "hydra_data.txt";

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
MassBalance_nonstorage(no_storage,t)
MassBalance_storage(storage,t)
MinFlow(i,j,t)
MaxFlow(i,j,t)
MaxStor(storage,t)
MinStor(storage,t)
Demand_eq(demand,t)
Objective
;

* Objective function for time step by time step formulation

Objective ..
    Z =E= SUM(t,SUM((i,j)$links(i,j), Q(i,j,t) * link_timeseries_data(t,i,j,"cost")));

*Calculating water delivery for each demand node at each time step

Demand_eq(demand,t)..
         delivery(demand,t) =E= SUM(j$links(j,demand), Q(j,demand,t));

* Mass balance constrait for non-storage nodes

MassBalance_nonstorage(no_storage,t) ..
    SUM(j$links(j,no_storage), Q(j,no_storage,t))
    - SUM(j$links(no_storage,j), Q(no_storage,j,t)*
      link_timeseries_data(t,no_storage,j,"flowmult"))
    - demand_scalar_data(no_storage,"consumption_coeff")$demand(no_storage) * delivery(no_storage,t)
    =E= 0;

* Storage constraint for storage nodes:

MassBalance_storage(storage,t)..

         SUM(j$links(j,storage), Q(j,storage,t))
         - SUM(j$links(storage,j), Q(storage,j,t) *
           link_timeseries_data(t,storage,j,"flowmult") )
         -S(storage,t)
         +S(storage,t--1)$(ord(t) GT 1)
         + surface_reservoir_scalar_data(storage,"init_stor")$(ord(t) EQ 1)
         =E= 0;

* Lower and upper bound of possible flow in links

MinFlow(i,j,t)$links(i,j) ..
    Q(i,j,t) =G= link_timeseries_data(t,i,j,"min_flow");

MaxFlow(i,j,t)$links(i,j) ..
    Q(i,j,t) =L= link_timeseries_data(t,i,j,"max_flow");

* Lower and upper bound of Storage volume at storage nodes
MaxStor(storage,t)..
    S(storage,t) =L= surface_reservoir_timeseries_data(t,storage,"max_stor");

MinStor(storage,t)..
    S(storage,t) =G= surface_reservoir_timeseries_data(t,storage,"min_stor");

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
