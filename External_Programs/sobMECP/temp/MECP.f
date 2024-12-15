      PROGRAM Optimizer
      implicit none

C     New version, Nov. 2003. All gradients converted to Hartree/Ang.
C     facPp chosen so that inverse Hessian ~ diagonal 0.7 Ang*Ang/Hartree

      INTEGER Natom, Nx
      parameter (Natom=numatom)
C         Set Natom to the number of atoms.
      parameter (Nx=3*Natom)

      INTEGER Nstep, FFile, Conv, AtNum(Natom)
      DOUBLE PRECISION Ea_1, Ea_2, Eb_1, Eb_2, IH_1(Nx,Nx), IH_2(Nx,Nx), ParG(Nx), PerpG(Nx)
      DOUBLE PRECISION Ga_1(Nx), Ga_2(Nx), Gb_1(Nx), Gb_2(Nx), X_1(Nx), X_2(Nx), X_3(Nx)
      DOUBLE PRECISION G_1(Nx), G_2(Nx)

      CALL ReadProgFile(Natom,Nx,AtNum,Nstep,FFile,X_1,X_2,IH_1,Ea_1,Eb_1,Ga_1,Gb_1,G_1)
C          Recover data from the previous Steps
      CALL ReadInput(Natom,Nx,Ea_2,Ga_2,Eb_2,Gb_2)
C          Read in the new ab initio Energies and Gradients
      CALL Effective_Gradient(Nx,Ea_2,Eb_2,Ga_2,Gb_2,ParG,PerpG,G_2)
C          Compute the Effective Gradient fac * DeltaE * PerpG + ParG
      CALL UpdateX(Nx,Nstep,FFile,X_1,X_2,X_3,G_1,G_2,IH_1,IH_2)
C          the BFGS step
      CALL TestConvergence(Nx,Natom,Nstep,AtNum,Ea_2,Eb_2,X_2,X_3,ParG,PerpG,G_2,Conv)
C          Checks Delta E, X, Mag. Delta G. Writes Output File
      IF (Conv .ne. 1) THEN
           CALL WriteGeomFile(Natom,Nx,AtNum,X_3)
           CALL WriteProgFile(Natom,Nx,AtNum,Nstep,X_2,X_3,IH_2,Ea_2,Eb_2,Ga_2,Gb_2,G_2)
      END IF

      END





       SUBROUTINE Effective_Gradient(N,Ea,Eb,Ga,Gb,ParG,PerpG,G)
       implicit none
       
C      Computes the parallel and perpendicular compenents of the Effective Gradient,
C      As well as the effective gradient itself.
       
       integer n, i
       double precision Ea, Eb, Ga(N), Gb(N), G(N), ParG(N), PerpG(N), npg, pp
       double precision facPP, facP
       parameter (facPP=140.d0,facP=1.d0)
C  These factors are only really important for the first step
C  The "difference gradient" is typically ca. 0.075 Hartree/Bohr.
C      i.e. 0.14 Hartree/Angstrom.
C  Assuming this is constant, this gives a Hessian term for the func (Ea-Eb)**2
C     of ca. 0.01 Hartree**2 / Angstrom**2  (0.14**2 / 2)
C  The Hessian term along "normal" coordinates is empirically about 1.4 Hartree / Angstrom**2
C  Using facPP ~ 140 /Hartree means that along this coordinate, too, the Hessian is about right.
       
       npg = 0.d0
       pp = 0.d0
       do i = 1, n
           PerpG(i) = Ga(i) - Gb(i)
           npg = npg + PerpG(i)**2
           pp = pp + Ga(i) * PerpG(i)
       end do
       npg = sqrt(npg)
       pp = pp / npg
       do i = 1, n
           ParG(i) = Ga(i) - PerpG(i) / npg * pp
           G(i) = (Ea - Eb) * facPP * PerpG(i) + facP * ParG(i)
       end do
       return
       
       END
       




      SUBROUTINE error_handling(e)
      implicit none

      integer e

      IF (e .eq. -1) THEN
          write (*,*) "The ProgFile does not exist for some reason."
          write (*,*) "Please create it then try again."
      END IF

      IF (e .eq. -2) THEN
          write (*,*) "Incomplete ProgFile - did you set Nstep right ?"
      END IF

      IF (e .eq. -3) THEN
          write (*,*) "Problem Reading Gaussian Output"
          OPEN(UNIT=302,FILE="AddtoReportFile")
          write (302,*) "ERROR IN GAUSSIAN STEP"
          CLOSE(302)
      END IF

      IF (e .eq. -4) THEN
           write (*,*) "Wrong Number of Atoms - Recompile !!"
      END IF

      IF (e .eq. -5) THEN
           write (*,*) "Problem with the ab initio Job."
      END IF

      STOP

      END





       SUBROUTINE Initialize(N,H,Ea,Eb,Ga,Gb)
       implicit none
       
       INTEGER i, j, n
       DOUBLE PRECISION H(N,N), Ea, Eb, Ga(N), Gb(N)
       
       Ea = 0.d0
       Eb = 0.d0
       do i = 1, n
           Ga(i) = 0.d0
           Gb(i) = 0.d0
           H(i,i) = .7d0
C Inverse Hessian values of .7 correspond to Hessians of 1.4 Hartree/Angstrom**2 - about right
           do j = i + 1, n
               H(i,j) = 0.d0
               H(j,i) = 0.d0
           end do
       end do
       return

       END





       SUBROUTINE ReadInput(natom,nx,Ea,Ga,Eb,Gb)
       implicit none
       
       INTEGER i, j, k, kk, natom, nx, error
       DOUBLE PRECISION Ea, Eb, Ga(Nx), Gb(Nx)
       CHARACTER*60 dummy
       DOUBLE PRECISION tmpg, bohr
       PARAMETER (bohr=0.529177d0)

       OPEN(UNIT=8,FILE="ab_initio")
       
       read (8,*) dummy
       read (UNIT=8,FMT=*,IOSTAT=error) Ea
       IF (error .ne. 0) THEN
            error = -5
            CALL error_handling(error)
       END IF
       read (8,*) dummy
       DO I = 1, natom
           k = 3 * (i - 1) + 1
           READ (UNIT=8,FMT=*,IOSTAT=error) kk, (Ga(J),J=k,k+2)
           IF (error .ne. 0) THEN
                error = -5
                CALL error_handling(error)
           END IF
       END DO
       read (8,*) dummy
C The gradient output by most programs is in fact the FORCE - convert here to gradient.
C Also, convert from Hartree/Bohr to Hartree/Ang
       DO i = 1, nx
           Ga(i) = -Ga(i) / bohr
       end do

       read (UNIT=8,FMT=*,IOSTAT=error) Eb
       read (8,*) dummy
       IF (error .ne. 0) THEN
            error = -5
            CALL error_handling(error)
       END IF
       DO I = 1, natom
           k = 3 * (i - 1) + 1
           READ (UNIT=8,FMT=*,IOSTAT=error) kk, (Gb(J),J=k,k+2)
           IF (error .ne. 0) THEN
                error = -5
                CALL error_handling(error)
           END IF
       END DO
       DO i = 1, nx
           Gb(i) = -Gb(i) / bohr
       end do

       CLOSE(8)
       return

       END




       SUBROUTINE ReadProgFile(natom,nx,AtNum,Nstep,FFile,X_1,X_2,HI,Ea,Eb,Ga,Gb,G)
       implicit none
       
       INTEGER natom, nx, AtNum(Natom), Nstep, i, j, k, error, FFile
       DOUBLE PRECISION X_1(Nx), X_2(Nx), HI(Nx,Nx), Ea, Eb, Ga(Nx), Gb(Nx), G(Nx)
       
       LOGICAL PGFok
       CHARACTER*80 dummy
       
       INQUIRE(FILE="ProgFile",EXIST=PGFok)
       IF (.not. PGFok) THEN
           error = -1
           CALL error_handling(error)
       END IF
       
       OPEN(UNIT=8,FILE="ProgFile")
       READ(8,*) dummy
       READ(8,*) dummy
       READ(8,*) i
       IF (i .ne. natom) then
           error = -4
           CALL error_handling(error)
       END IF
       READ(8,*) dummy
       READ(8,*) Nstep
       READ(8,*) dummy
       READ(8,*) FFile
       
       READ(8,*) dummy
       DO I = 1, natom
           k = 3 * (i - 1) + 1
           READ(8,*) AtNum(I), (X_2(J),J=k,k+2)
       END DO
       
       IF ((Nstep .eq. 0) .AND. (FFile .eq. 0)) THEN
C First step - the ProgFile is incomplete. To avoid problems,
C there are 'existence' tests in the next input lines so
C as to crash the program if Nstep > 0 yet the file is incomplete.
           CALL Initialize(Nx,HI,Ea,Eb,Ga,Gb)
           CLOSE(8)
           RETURN
       END IF
       
       READ(UNIT=8,FMT=*,IOSTAT=error) dummy
       IF (error .ne. 0) THEN
           error = -2
           CALL error_handling(error)
       END IF
       DO I = 1, Natom
           k = 3 *(I-1) + 1
           READ(UNIT=8,FMT=*,IOSTAT=error) (X_1(J),J=k,k+2)
C Geometries are in Angstrom - fine!
           IF (error .ne. 0) THEN
               error = -2
               CALL error_handling(error)
           END IF
       END DO
       READ(8,*) dummy
       READ(8,*) Ea
       READ(8,*) Eb
       READ(8,*) dummy
       DO I = 1, nx
           READ(8,*) Ga(I)
       END DO
       READ(8,*) dummy
       DO I = 1, nx
           READ(8,*) Gb(I)
       END DO
       READ(8,*) dummy
       DO I = 1, nx
           READ(8,*) G(I)
       END DO
       READ(8,*) dummy
       DO I = 1, nx
           DO J = 1, nx
               READ(8,*) HI(I,J)
           END DO
       END DO
       CLOSE(8)
       return

       END




      SUBROUTINE TestConvergence(N,Natom,Nstep,AtNum,Ea,Eb,X_2,X_3,ParG,PerpG,G,Conv)
      implicit none

C     Checks convergence, and updates report file
C     There are 5 criteria for testing convergence
C     They are the same as in Gaussian (Except the last):
C     Av.DeltaX, Max.DeltaX, Av.Grad., Max.Grad., DeltaE

      INTEGER N, Natom, AtNum(Natom), Nstep, Conv, i, j, k
      DOUBLE PRECISION Ea, Eb, X_2(N), ParG(N), PerpG(N), X_3(N), G(N)

      CHARACTER*3 flags(5)
      LOGICAL PConv(5)
      DOUBLE PRECISION DeltaX(N), DE, DXMax, DXRMS, GMax, GRMS, PpGRMS, PGRMS, TDE
      DOUBLE PRECISION TDXMax, TDxRMS, TGMax, TGRMS
      PARAMETER (TDE=5.d-5,TDXMax=4.d-3,TDXRMS=2.5d-3,TGMax=7.d-4,TGRMS=5.d-4)

      OPEN(UNIT=8,FILE="AddtoReportFile")
      IF (Nstep .eq. 0) THEN
          write (8,*) "      Geometry Optimization of an MECP"
          write (8,*) "      Program: J. N. Harvey, March 1999"
          write (8,*) "        version 2, November 2003"
          write (8,*) "      Adapted by Tian Lu (sobereva@sina.com)  March 15, 2015"
          write (8,*)
          write (8,'(A)') "Initial Geometry:"
          DO I = 1, Natom
              k = 3 * (I-1) + 1
              write (8,'(I3,3F15.7)') AtNum(I), (X_2(j),j=k,k+2)
          END DO
          write (8,*)
      END IF
      DE = ABS(Ea - Eb)
      DXMax = 0.d0
      DXRMS = 0.d0
      GMax = 0.d0
      GRMS = 0.d0
      PpGRMS = 0.d0
      PGRMS = 0.d0
      DO I = 1, n
          DeltaX(i) = X_3(i) - X_2(i)
          IF (ABS(DeltaX(i)) .gt. DXMax) DXMax = ABS(DeltaX(i))
          DXRMS = DXRMS + DeltaX(i)**2
          IF (ABS(G(i)) .gt. Gmax) Gmax = ABS(G(i))
          GRMS = GRMS + G(i)**2
          PpGRMS = PpGRMS + PerpG(i)**2
          PGRMS = PGRMS + ParG(i)**2
      END DO
      DXRMS = SQRT(DXRMS / N)
      GRMS = SQRT(GRMS / N)
      PpGRMS= SQRT(PpGRMS / N)
      PGRMS = SQRT(PGRMS / N)

      Conv = 0
      do i = 1, 5
          flags(i) = " NO"
          PConv(i) = .false.
      end do

      IF (GMax .lt. TGMax) THEN
          PConv(1) = .true.
          flags(1) = "YES"
      END IF
      IF (GRMS .lt. TGRMS) THEN
          PConv(2) = .true.
          flags(2) = "YES"
      END IF
      IF (DXMax .lt. TDXMax) THEN
          PConv(3) = .true.
          flags(3) = "YES"
      END IF
      IF (DXRMS .lt. TDXRMS) THEN
          PConv(4) = .true.
          flags(4) = "YES"
      END IF
      IF (DE .lt. TDE) THEN
          PConv(5) = .true.
          flags(5) = "YES"
      END IF
      IF (PConv(1) .and. PConv(2) .and. PConv(3) .and. PConv(4) .and. PConv(5)) THEN
          Conv = 1
      ELSE
          Nstep = Nstep + 1
      END IF

      write (8,'(A,F18.10)') "Energy of First State:  ",Ea
      write (8,'(A,F18.10)') "Energy of Second State: ",Eb
      write (8,*)
      write (8,'(A)') "Convergence Check (Actual Value, then Threshold, then Status):"
      write (8,'(A,F11.6,A,F8.6,A,A)') "Max Gradient El.:", GMax," (",TGMax,")  ",flags(1)
      write (8,'(A,F11.6,A,F8.6,A,A)') "RMS Gradient El.:", GRMS," (",TGRMS,")  ",flags(2)
      write (8,'(A,F11.6,A,F8.6,A,A)') "Max Change of X: ",DXMax," (",TDXMax,")  ",flags(3)
      write (8,'(A,F11.6,A,F8.6,A,A)') "RMS Change of X: ",DXRMS," (",TDXRMS,")  ",flags(4)
      write (8,'(A,F11.6,A,F8.6,A,A)') "Difference in E: ",DE," (",TDE,")  ",flags(5)
      write (*,*)
      write (*,'(A,F11.6,A,F8.6,A,A)') "Max Gradient El.:", GMax," (",TGMax,")  ",flags(1)
      write (*,'(A,F11.6,A,F8.6,A,A)') "RMS Gradient El.:", GRMS," (",TGRMS,")  ",flags(2)
      write (*,'(A,F11.6,A,F8.6,A,A)') "Max Change of X: ",DXMax," (",TDXMax,")  ",flags(3)
      write (*,'(A,F11.6,A,F8.6,A,A)') "RMS Change of X: ",DXRMS," (",TDXRMS,")  ",flags(4)
      write (*,'(A,F11.6,A,F8.6,A,A)') "Difference in E: ",DE," (",TDE,")  ",flags(5)
      write (*,*)
      write (8,'(A)') "Overall Effective Gradient:"
      DO I = 1, Natom
          k = 3 * (I - 1) + 1
          write (8,'(I3,3F16.8)') I, (G(J),J=k,k+2)
      END DO
      write (8,*)
      write (8,'(A,F11.6,A)') "Difference Gradient: (RMS * DE:",PpGRMS,")"
      DO I = 1, Natom
          k = 3 * (I - 1) + 1
          write (8,'(I3,3F16.8)') I, (PerpG(J),J=k,k+2)
      END DO
      write (8,*)
      write (8,'(A,F11.6,A)') "Parallel Gradient: (RMS:",PGRMS,")"
      DO I = 1, Natom
          k = 3 * (I - 1) + 1
          write (8,'(I3,3F16.8)') I, (ParG(J),J=k,k+2)
      END DO
      write (8,*)

      IF (Conv .eq. 1) THEN
          write (8,'(A)') "The MECP Optimization has CONVERGED at that geometry !!!"
          write (8,'(A)') "Goodbye and fly with us again..."
      ELSE
          write (8,'(A,I3)') "Geometry at Step",Nstep
          DO I = 1, Natom
              k = 3 * (I - 1) + 1
              write (8,'(I3,3F15.7)') AtNum(I), (X_3(J),J=k,k+2)
          END DO
          write (8,*)
      END IF

      CLOSE(8)
      return

      END



       SUBROUTINE UpdateX(N,Nstep,FFile,X_1,X_2,X_3,G_1,G_2,HI_1,HI_2)
       implicit none
       
       ! Specially Adapted BFGS routine from Numerical Recipes
       
       integer i, j, k, n, Nstep, FFile
       double precision X_1(N), X_2(N), G_1(N), G_2(N), HI_1(N,N), X_3(N), HI_2(N,N)
       
       double precision stpmax, DelG(N), HDelG(N), ChgeX(N), DelX(N), w(N), fac,
     & fad, fae, sumdg, sumdx, stpl, lgstst, STPMX
       parameter (STPMX = 0.1d0)
       
       stpmax = STPMX * N
       IF ((Nstep .eq. 0) .and. (FFile .eq. 0)) THEN
           DO i = 1, n
               ChgeX(i) = -.7d0 * G_2(i)
               DO j = 1, n
                   HI_2(i,j) = HI_1(i,j)
               end do
           end do
       ELSE
           DO i = 1, n
               DelG(i) = G_2(i) - G_1(i)
               DelX(i) = X_2(i) - X_1(i)
           end do
           do i = 1, n
               HDelG(i) = 0.d0
               do j = 1, n
                   hdelg(i) = hdelg(i) + HI_1(i,j) * DelG(j)
               end do
           end do
           fac = 0.d0
           fae = 0.d0
           sumdg = 0.d0
           sumdx = 0.d0
           do i = 1, n
               fac = fac + delg(i) * delx(i)
               fae = fae + delg(i) * hdelg(i)
               sumdg = sumdg + delg(i)**2
               sumdx = sumdx + delx(i)**2
           end do
           fac = 1.d0 / fac
           fad = 1.d0 / fae
           do i = 1, n
               w(i) = fac * DelX(i) - fad * HDelG(i)
           end do
           DO I = 1, N
               do j = 1, n
                   HI_2(i,j) = HI_1(i,j) + fac * delx(i) * delx(j) -
     &                fad * HDelG(I) * HDelG(j) + fae * w(i) * w(j)
               end do
           end do
           do i = 1, n
               ChgeX(i) = 0.d0
               do j = 1, n
                   ChgeX(i) = ChgeX(i) - HI_2(i,j) * G_2(j)
               end do
           end do
       END IF
       
       fac = 0.d0
       do i = 1, n
           fac = fac + ChgeX(i)**2
       end do
       stpl = SQRT(fac)
       IF (stpl .gt. stpmax) THEN
           do i = 1, n
               ChgeX(i) = ChgeX(i) / stpl * stpmax
           end do
       END IF
       lgstst = 0.d0
       do i = 1, n
            IF (ABS(ChgeX(i)) .gt. lgstst) lgstst = ABS(ChgeX(i))
       end do
       IF (lgstst .gt. STPMX) THEN
           do i = 1, n
               ChgeX(i) = ChgeX(i) / lgstst * STPMX
           end do
       END IF
       do i = 1, n
           X_3(i) = X_2(i) + ChgeX(i)
       end do
       
       END


      SUBROUTINE WriteGeomFile(Natom,Nx,AtNum,X)
      implicit none

      INTEGER i, j, Natom, Nx, AtNum(Natom)
      DOUBLE PRECISION X(Nx)

      OPEN (UNIT=8,FILE="geom")
      DO I = 1, Natom
          write (8,'(I4,3F14.8)') AtNum(I), (X(J),J=3*(I-1)+1,3*(I-1)+3)
      END DO
      write (8,*)
      CLOSE(8)
      return

      END



      SUBROUTINE WriteProgFile(natom,nx,AtNum,Nstep,X_2,X_3,HI,Ea,Eb,Ga,Gb,G)
      implicit none

      INTEGER natom, nx, AtNum(Natom), Nstep
      DOUBLE PRECISION X_2(Nx), X_3(Nx), HI(Nx,Nx), Ea, Eb, Ga(Nx), Gb(Nx), G(Nx)

      INTEGER I, J

      OPEN(UNIT=8,FILE="ProgFile")
      WRITE(8,*) "Progress File for MECP Optimization"
      WRITE(8,*) "Number of Atoms:"
      WRITE(8,*) Natom
      WRITE(8,*) "Number of Steps already Run"
      WRITE(8,*) Nstep
      WRITE(8,*) "Is this a full ProgFile ?"
      WRITE(8,*) 1

      WRITE(8,*) "Next Geometry to Compute:"
      DO I = 1, natom
          WRITE(8,'(I3,3F20.12)') AtNum(I), (X_3(J),J=3*(I-1)+1,3*(I-1)+3)
      END DO

      WRITE(8,*) "Previous Geometry:"
      DO I = 1, Natom
          write (8,'(3F20.12)') (X_2(J),J=3*(I-1)+1,3*(I-1)+3)
      END DO
      WRITE(8,*) "Energies of First, Second State at that Geometry:"
      WRITE(8,'(F20.12)') Ea
      WRITE(8,'(F20.12)') Eb
      WRITE(8,*) "Gradient of First State at that Geometry:"
      DO I = 1, nx
          WRITE(8,'(F20.12)') Ga(I)
      END DO
      WRITE(8,*) "Gradient of Second State at that Geometry:"
      DO I = 1, nx
          WRITE(8,'(F20.12)') Gb(I)
      END DO
      WRITE(8,*) "Effective Gradient at that Geometry:"
      DO I = 1, nx
          WRITE(8,'(F20.12)') G(I)
      END DO
      WRITE(8,*) "Approximate Inverse Hessian at that Geometry:"
      DO I = 1, nx
          DO J = 1, nx
              WRITE(8,'(F20.12)') HI(I,J)
          END DO
      END DO

      CLOSE(8)
      return

      END
