c
c -----------------------------------------------------------
c
       subroutine setPhysBndry(rectflags,ilo,ihi,jlo,jhi,mbuff,level)

       use amr_module
       implicit double precision (a-h, o-z)

       dimension rectflags(ilo-mbuff:ihi+mbuff, jlo-mbuff:jhi+mbuff)

c ****************************************************************
c  setPhysBndry = if grid borders the physical domain then
c                 any flagged points sticking out are okay
c ****************************************************************

       if (ilo .eq. 0 .and. .not. xperdom) then
c       set left flagged points to be ok
          do j = jlo-mbuff, jhi+mbuff
            do i = ilo-mbuff, ilo-1
             rectflags(i,j) = abs(rectflags(i,j))
            end do
          end do
       endif

       if (ihi .eq. iregsz(level)-1 .and. .not. xperdom) then
c       set right flagged points to be ok
          do j = jlo-mbuff, jhi+mbuff
            do i = ihi+1, ihi+mbuff
             rectflags(i,j) = abs(rectflags(i,j))
            end do
          end do
       endif

 
       if (jlo .eq. 0 .and. .not. yperdom) then
c       set bottom flagged points to be ok
          do i = ilo-mbuff, ihi+mbuff
            do j = jlo-mbuff, jlo-1    
             rectflags(i,j) = abs(rectflags(i,j))
            end do
          end do
       endif

       if (jhi .eq. jregsz(level)-1 .and. .not. yperdom) then
c       set top flagged points to be ok
          do i = ilo-mbuff, ihi+mbuff
            do j = jhi+1, jhi+mbuff
             rectflags(i,j) = abs(rectflags(i,j))
            end do
          end do
       endif

       return
       end
