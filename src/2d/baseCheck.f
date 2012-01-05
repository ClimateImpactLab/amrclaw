
       logical function baseCheck(mnew,lbase,ilo,ihi,jlo,jhi)

       use amr_module
       implicit double precision (a-h, o-z)

       dimension ist(3),iend(3),jst(3),jend(3),ishift(3),jshift(3)
       ixproj(kk,ll) = (kk + ll*iabs(kk))/ll - iabs(kk)

c      index into alloc from iclo:ichi and jclo:jchi, not 0..leni/j. 
       iadd(i,j) = locm + i - iclo + leni*(j-jclo) 

c ::::::::::::::::::: baseCheck :::::::::::::::::::::::::::
c
c baseCheck - check that potential grid mnew is completely contained
c             in  coarser grids at level 'lbase' (>1) that will
c             stay fixed during this regridding step
c
c   this version tries to do it without using domflags
c   slower but better if cant afford memory over entire domain
c
c   mcheck is one bigger since for proper nesting, cell must be
c   at least one away from boundary of a parent grid, unless
c   on a domain boundary
c :::::::::::::::::::::::::::::::::::::::::::::::::::::::::

c       write(*,*)"NESTCK2 testing grid ",mnew,
c     .           " from ",ilo,ihi," to ",jlo,jhi

       levnew = node(nestlevel,mnew)
c
c initialize for potential periodicity
c each patch divided into 9 regions (some may be empty)
c e.g. i from (ilo,-1), (0,iregsz(level)-1),(iregsz(level),ihi)
c except using enlarged grid (ilo-1 to ihi+1)
       ist(1) = ilo-1
       ist(2) = 0
       ist(3) = iregsz(levnew)
       iend(1) = -1
       iend(2) = iregsz(levnew)-1
       iend(3) = ihi+1
       jst(1) = jlo-1
       jst(2) = 0
       jst(3) = jregsz(levnew)
       jend(1) = -1
       jend(2) = jregsz(levnew)-1
       jend(3) = jhi+1

       if (xperdom) then
          iishift = iregsz(levnew) 
       else 
          iishift = 0 
       endif
       if (yperdom) then
          jjshift = jregsz(levnew)
       else
          jjshift = 0
       endif
       ishift(1) = iishift
       ishift(2) = 0
       ishift(3) = -iishift
       jshift(1) = jjshift
       jshift(2) = 0
       jshift(3) = -jjshift

c
c    on to initializing for the given grid and its nest checking
       levratx = 1
       levraty = 1
       do 5 lev = lbase, levnew-1
          levratx = levratx * intratx(lev)
          levraty = levraty * intraty(lev)
 5     continue

c widen by 1 cell (proper nesting), then project to lbase
       iclo = ixproj(ilo-1,levratx)
       ichi = ixproj(ihi+1,levratx)
       jclo = ixproj(jlo-1,levraty)
       jchi = ixproj(jhi+1,levraty)
c       write(*,*)" coarsened grid from ",iclo,ichi," to ",jclo,jchi

       leni = ichi - iclo + 1
       lenj = jchi - jclo + 1
       lenrect = leni * lenj
       locm = igetsp(lenrect)
c      initialize on projected size of new grid. used to mark nesting         
       do k = 0, lenrect-1   
          alloc(locm + k) = 0.
       end do
c
c      corners dont count for nesting so mark as ok
        alloc(iadd(iclo,jclo)) = 1.
        alloc(iadd(iclo,jchi)) = 1.
        alloc(iadd(ichi,jclo)) = 1.
        alloc(iadd(ichi,jchi)) = 1.
c
c  if mnew on domain boundary fix flags so ok. 
c  fix extra border, and first/last real edge
       if (ilo .eq. 0 .and. .not. xperdom) then
         do j = jclo,jchi
            alloc(iadd(iclo,j)) = 1.
            alloc(iadd(iclo+1,j)) = 1.
         end do

       endif
       if (ihi .eq. iregsz(levnew)-1 .and. .not. xperdom) then
          do j = jclo, jchi
             alloc(iadd(ichi,j)) = 1.
             alloc(iadd(ichi-1,j)) = 1.
          end do
       endif
       if (jlo .eq. 0 .and. .not. yperdom) then
         do i = iclo,ichi
            alloc(iadd(i,jclo)) = 1.
            alloc(iadd(i,jclo+1)) = 1.
         end do
       endif
       if (jhi .eq. jregsz(levnew)-1 .and. .not. yperdom) then
          do i = iclo, ichi
             alloc(iadd(i,jchi)) = 1.
             alloc(iadd(i,jchi-1)) = 1.
          end do
       endif

       mptr = lstart(lbase)
 20       iblo = node(ndilo, mptr)
          ibhi = node(ndihi, mptr)
          jblo = node(ndjlo, mptr)
          jbhi = node(ndjhi, mptr)

c          write(*,*)
c          write(*,*)"TESTING AGAINST GRID ",mptr,
c     .              " from ",iblo,ibhi," to ",jblo,jbhi

c          compare all regions of patch with one lbase grid at a time
           do 25 i = 1, 3
              i1 = max(ilo-1,ist(i))
              i2 = min(ihi+1, iend(i))
           do 25 j = 1, 3
              j1 = max(jlo-1, jst(j))
              j2 = min(jhi+1, jend(j))
c              write(*,*)"region ",i,j," from ",i1,i2," to ",j1,j2
           
              if (.not. ((i1 .le. i2) .and. (j1 .le. j2))) go to 25
c
c             patch not empty. project coords to level lbase
              iplo = ixproj(i1+ishift(i),levratx)
              iphi = ixproj(i2+ishift(i),levratx)
              jplo = ixproj(j1+jshift(j),levraty)
              jphi = ixproj(j2+jshift(j),levraty)
c              write(*,*)"projected coords of region ",i,j,
c     .                  " is ",iplo,iphi," by ",jplo,jphi

              ixlo = max(iplo,iblo)
              ixhi = min(iphi,ibhi)
              jxlo = max(jplo,jblo)
              jxhi = min(jphi,jbhi)

c              write(*,*)"intersected reg ",ixlo,ixhi," by ",jxlo,jxhi
c FOR NOW DO NOT HANDLE PERIODIC NEST CHECKING
          
              if (.not.((ixlo.le.ixhi) .and. (jxlo.le.jxhi))) go to 25
c              write(*,*) "SETTING from ",ixlo,ixhi,jxlo,jxhi
c              write(*,*) "shifts are ", ishift(i),jshift(j)
c     mark intersected regions with 1
              do jx = jxlo, jxhi
              do ix = ixlo, ixhi
c              need to mark nesting of orig coords, not shifted 
               alloc(iadd(ix-ishift(i)/levratx,jx-jshift(j)/levraty))=1.
              end do
              end do

 25       continue

 30       mptr = node(levelptr, mptr)
          if (mptr .ne. 0) go to 20

c     output for debugging
c       do 34 jj = jclo, jchi
c           j = jchi + jclo - jj
c           write(*,344)(int(alloc(iadd(i,j))), i=iclo,ichi) 
c 344       format(110i1)
c 34    continue

c
c  if any zeroes left mnew not nested
c
       do 40 j = jclo, jchi
       do 40 i = iclo, ichi
          if (alloc(iadd(i,j)) .eq. 0) then
             baseCheck = .false.
             go to 99
          endif
 40    continue

c      if made it here then grid is nested
       baseCheck = .true.

 99    call reclam(locm, lenrect)

       return 
       end
