$TITLE    Demo2.gms

* version: time-step by time-step

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
Q(i,j,t) flow in each link in each period
S(i,t) storage volume in storage nodes
delivery (i) water delivered to demand node i in each period
Z objective function
Obj (t);
;

POSITIVE VARIABLES
Q
S
;

positive variable  storage(i,t) an interim variable for saving the value of the storage at the end of each time-step;

EQUATIONS
MassBalance_nonstorage(ns_nodes)
MassBalance_storage(s_nodes)
MinFlow(i,j,t)
MaxFlow(i,j,t)
MaxStor(s_nodes,t)
MinStor(s_nodes,t)
Demand(dem_nodes)
Objective
;

* introducing a dummy variable to empty (reset) the time-step in each loop

$onempty
set dv(t) / /;

* Objective function for time step by time step formulation

Objective ..
    Z =E=sum(t$dv(t),SUM((i,j)$links(i,j), Q(i,j,t) * cost(i,j,t)));

*Calculating water delivery for each demand node at each time step

Demand(dem_nodes)..
         delivery(dem_nodes) =E= sum(t$dv(t),SUM(j$links(j,dem_nodes), Q(j,dem_nodes,t)
         * flowmultiplier(j,dem_nodes,t)));

* Mass balance constrait for non-storage nodes:

MassBalance_nonstorage(ns_nodes) ..
    sum(t$dv(t),inflow(ns_nodes,t)+SUM(j$links(j,ns_nodes), Q(j,ns_nodes,t)* flowmultiplier(j,ns_nodes,t))
    - SUM(j$links(ns_nodes,j), Q(ns_nodes,j,t))
    - cc(ns_nodes)$dem_nodes(ns_nodes) * delivery(ns_nodes))
    =E= 0;

* Mass balance constraint for storage nodes:

MassBalance_storage(s_nodes)..
         sum(t$dv(t),inflow(s_nodes,t)+SUM(j$links(j,s_nodes), Q(j,s_nodes,t)* flowmultiplier(j,s_nodes,t))
         - SUM(j$links(s_nodes,j), Q(s_nodes,j,t))
         -S(s_nodes,t)
         +storage(s_nodes,t-1)$(ord(t) GT 1)
         + initStor(s_nodes,t)$(ord(t) EQ 1))
         =E= 0;

* Lower and upper bound of possible flow in links

MinFlow(i,j,t)$(links(i,j) and dv(t))..
    Q(i,j,t) =G= lower(i,j,t);

MaxFlow(i,j,t)$(links(i,j) and dv(t))..
    Q(i,j,t) =L= upper(i,j,t);

* Lower and upper bound of Storage volume at storage nodes

MaxStor(s_nodes,t)$dv(t)..
    S(s_nodes,t) =L= storageupper(s_nodes,t);

MinStor(s_nodes,t)$dv(t)..
    S(s_nodes,t) =G= storagelower(s_nodes,t);

** ----------------------------------------------------------------------
**  Model declaration and solve statements
** ----------------------------------------------------------------------

MODEL Demo2 /ALL/;

loop (tsteps,
            dv(tsteps)=t(tsteps);
            display dv;
            SOLVE Demo2 USING LP MINIMIZING Z;
            storage.fx(i,tsteps)=S.l(i,tsteps) ;
            Obj.l(tsteps)=Z.l;
            DISPLAY  Z.l, Obj.l,storage.l,S.l, Q.l,delivery.l;
            dv(tsteps)=no;
      );

*Generating results output

execute_unload "Results.gdx" ,
    Q,
    S,
    MassBalance_storage,
    MassBalance_nonstorage,
    MinFlow,
    MaxFlow,
    MinStor,
    MaxStor,
    Z,
    Obj,
    cost,
    storage,
    delivery,
    inflow;
