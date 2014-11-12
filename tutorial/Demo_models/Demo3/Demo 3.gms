$TITLE    Demo3.gms

* version: time-step by time-step

 option limrow=10000;
 option limcol=10000;

** ----------------------------------------------------------------------
**  Loading Data: sets, parameters and tables
** ----------------------------------------------------------------------

$        include "dataset 2.txt";

** ----------------------------------------------------------------------
**  Model variables and equations
** ----------------------------------------------------------------------

VARIABLES
Q(i,j,t) flow in each link in each period
S(i,t) storage volume in storage nodes
delivery (i) water delivered to demand node i in each period
Z objective function
Obj (t)
;

POSITIVE VARIABLES
Q
S
alpha(i) target demand satisfaction ratio ;

alpha.up(dem_nodes)=1;

positive variable  storage(s_nodes,t) an interim variable for saving the value of the storage at the end of each time-step;
positive variable  a(i,t) an interim variable for saving the value of the satisfaction ratio at the end of each time-step;

EQUATIONS
MassBalance_storage(s_nodes)
MinFlow(i,j,t)
MaxFlow(i,j,t)
MaxStor(s_nodes,t)
MinStor(s_nodes,t)
Demand_satisfaction_ratio(i,t)
Objective
;

* introducing a dummy variable to empty (reset) the time-step in each loop

$onempty
set dv(t) / /;


* Objective function for time step by time step formulation

Objective ..
    Z =E= sum(t$dv(t),SUM((dem_nodes), alpha(dem_nodes) * cost(dem_nodes,t)));


*Calculating demand satisfaction ratio for each demand node in each time period

Demand_satisfaction_ratio(i,t)$(dv(t)and not s_nodes(i))..
         (alpha(i)* D(i,t))$dem_nodes(i)=E= SUM(j$links(j,i), Q(j,i,t)* flowmultiplier(j,i,t))
                                         -SUM(j$links(i,j), Q(i,j,t));

* Mass balance constraint for storage nodes:

MassBalance_storage(s_nodes)..

         sum(t$dv(t),inflow(s_nodes,t)+SUM(j$links(j,s_nodes), Q(j,s_nodes,t)* flowmultiplier(j,s_nodes,t))
         - SUM(j$links(s_nodes,j), Q(s_nodes,j,t) )
         -S(s_nodes,t)
         +storage(s_nodes,t-1)$(ord(t) GT 1)
         + initStor(s_nodes,t)$(ord(t) EQ 1))
         =E= 0;

* Lower and upper bound of possible flow in links

MinFlow(i,j,t)$(links(i,j) and dv(t)) ..
    Q(i,j,t) =G= lower(i,j,t);

MaxFlow(i,j,t)$(links(i,j)  and dv(t))..
    Q(i,j,t) =L= upper(i,j,t);

* Lower and upper bound of Storage volume at storage nodes
MaxStor(s_nodes,t)$dv(t)..
    S(s_nodes,t) =L= storageupper(s_nodes,t);

MinStor(s_nodes,t)$dv(t)..
    S(s_nodes,t) =G= storagelower(s_nodes,t);

** ----------------------------------------------------------------------
**  Model declaration and solve statements
** ----------------------------------------------------------------------

MODEL Demo3 /ALL/;

loop (tsteps,
            dv(tsteps)=t(tsteps);
            display dv;
            SOLVE Demo3 USING LP MAXIMIZING Z;
            storage.fx(s_nodes,tsteps)=S.l(s_nodes,tsteps) ;
            a.l(i,tsteps)=alpha.l(i);
            Obj.l(tsteps)=Z.l;
            DISPLAY  Z.l, Obj.l,storage.l,S.l, Q.l;
            dv(tsteps)=no;
      );

*Generating results output

execute_unload "Results.gdx" ,
    Q,
    S,
    MassBalance_storage,
    MinFlow,
    MaxFlow,
    MinStor,
    MaxStor,
    Z,
    alpha,
    Obj,
    storage,
    a;



