* Price dependent electricity exchange with third countries:

+ SUM(IR, SUM((IS3,T), IHOURFRAC*IHOURSINST(IS3,T)*
   ( SUM(X3VPLACE$X3VX(IR,X3VPLACE),SUM(X3VSTEP,VX3VIM_T(Y,IR,X3VPLACE,X3VSTEP,IS3,T)*IX3VPIM_Y(Y,IR,X3VPLACE,X3VSTEP,IS3,T)))
    -SUM(X3VPLACE$X3VX(IR,X3VPLACE),SUM(X3VSTEP,VX3VEX_T(Y,IR,X3VPLACE,X3VSTEP,IS3,T)*IX3VPEX_Y(Y,IR,X3VPLACE,X3VSTEP,IS3,T))))))
* LARS: Added the shadow price to the balance constraint.
*     + SUM(IR, SUM((IS3,T), IHOURSINST(IS3,T)*
*        ( SUM(X3VPLACE$X3VX(IR,X3VPLACE),SUM(X3VSTEP,VX3VIM_T(Y,IR,X3VPLACE,X3VSTEP,IS3,T)*IX3VBALSP(X3VPLACE)))
*          -SUM(X3VPLACE$X3VX(IR,X3VPLACE),SUM(X3VSTEP,VX3VEX_T(Y,IR,X3VPLACE,X3VSTEP,IS3,T)*IX3VBALSP(X3VPLACE))))))







