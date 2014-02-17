! File array.f90
! $UWHPSC/codes/fortran/sub3.f90

module hog

contains 

subroutine angHist(dx, dy, binSize, hist)
  ! compute f(x) = x**2 for all elements of the array x. 
  implicit none
  ! I/O
  real(kind=8), dimension(:,:), intent(in) :: dx, dy
  integer, intent(in) :: binSize
  real(kind=8), dimension(binSize), intent(out) :: hist

  ! dummy variables
  real(kind=8), dimension(size(dx,1), size(dx,2)) :: mag
  integer, dimension(size(dx,1), size(dx,2)) :: ang
  real(kind=8) :: pi, eps
  integer :: i, m, p

  ! constants
  pi = 3.14159265358979323846
  eps = 0.0000000000000000001
  

  ! magnitude and angles
  mag = sqrt(dx ** 2 + dy ** 2)
  ang = floor((atan2(dy, dx) + pi) / (2 * pi + eps) * binSize)

  ! initialize hist as zero
  hist = 0.0_8

  do i=1,size(ang,1)
    do m=1,size(ang,2)
      p = ang(i,m) + 1 ! fortran counts from 1 to end (incl)
      hist(p) = hist(p) + mag(i,m)
    enddo
  enddo

  ! normalize hist
  hist = hist / (size(ang,1) * size(ang,2))
    
end subroutine angHist

subroutine angHist2(img, binSize, hist)
  ! compute f(x) = x**2 for all elements of the array x. 
  implicit none
  ! I/O variables
  real(kind=8), dimension(:,:), intent(in) :: img
  integer, intent(in) :: binSize
  real(kind=8), dimension(binSize), intent(out) :: hist

  ! dummy variables
  real(kind=8), dimension(size(img,1),size(img,2)) :: dx, dy, mag
  integer, dimension(size(img,1),size(img,2)) :: ang
  real(kind=8) :: pi, eps
  integer :: i, m, p, l

  ! constants
  pi = 3.14159265358979323846
  eps = 0.0000000000000000001

  ! initialize hist
  hist = 0.0_8
  
  ! compute dx as numpy.gradient does
  dx(1,:) = img(2,:) - img(1,:)
  do i=3,size(img,1)
    dx(i-1,:) = (img(i,:) - img(i-2,:)) / 2.0
  enddo
  l = size(img,1)
  dx(l,:) = img(l,:) - img(l-1,:)

  ! compute dy as numpy.gradient does
  dy(:,1) = img(:,2) - img(:,1)
  do i=3,size(img,2)
    dy(:, i-1) = (img(:,i) - img(:,i-2)) / 2.0
  enddo
  l = size(img,2)
  dy(:,l) = img(:,l) - img(:,l-1)

  ! compute magnitude and angle of gradients  
  mag = sqrt(dx ** 2 + dy ** 2)
  ang = floor((atan2(dy, dx) + pi) / (2 * pi + eps) * binSize)

  ! bin them
  do i=1,size(ang,1)
    do m=1,size(ang,2)
      p = ang(i,m) + 1 ! fortran counts from 1 to end (incl)
      hist(p) = hist(p) + mag(i,m)
    enddo
  enddo

  ! normalize hist
  hist = hist / (size(ang,1) * size(ang,2))
    
end subroutine angHist2

end module hog