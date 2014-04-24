function [ feats ] = generateTrajFeatures( traj )
% traj is 2D matrix numFrames*[X Y]
% feats is a numFrames * 8 matrix
% feats is the feature matrix from Burgos-Artizzu CVPR 2012 - top Pg 6

% TODOs
% not sure about deltaT or atan
% brittle - very susceptible to bad trajectories and NaNs
% extend to two object features

% position
f1 = [traj];

% direction
f2_1 = (traj(:,2) - [0; traj(1:end-1,2)]) ./ (traj(:,1) - [0; traj(1:end-1,1)]);
f2_1(isnan(f2_1)) = 0; % correct?
f2_1 = atan(f2_1); %correct?

% dir change
f3_1 = f2_1 - [0; f2_1(1:end-1)];

% velocity
x1_d = (traj(:,1) - [0; traj(1:end-1,1)]);
y1_d = (traj(:,2) - [0; traj(1:end-1,2)]);
deltaT = (1/3); % ?? not sure what this is supposed to be

f4_x1 = deltaT*(0.25*[0; x1_d(1:end-1,:)] + 0.5*x1_d +0.25*[x1_d(2:end,:); 0]);
f4_y1 = deltaT*(0.25*[0; y1_d(1:end-1,:)] + 0.5*y1_d +0.25*[y1_d(2:end,:); 0]);

% acceleration
deltaT2 = 1/(2*2); % ?? not sure what this is
f5_x1 = ([f4_x1(2:end) ; 0] - [0; f4_x1(1:end-1)])*deltaT2;
f5_y1 = ([f4_y1(2:end) ; 0] - [0; f4_y1(1:end-1)])*deltaT2;

feats = [f1, f2_1, f3_1, f4_x1, f4_y1, f5_x1, f5_y1,]; 