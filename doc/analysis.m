%% Parameters
A1 = 28; A3 = 28;
A2 = 32; A4 = 32;
A = [A1 A2 A3 A4];

a1 = 0.071; a3 = 0.071;
a2 = 0.057; a4 = 0.057;
a = [a1 a2 a3 a4];

k1 = 3.33; k2 = 3.33;
g = 981;

% ????
kc = 1;

gamma1 = 0.4;
gamma2 = 0.2;

%% Linearization point
h0 = [40 40 40 40];
u0 = [0 0];

%% Matrices from the guide TODO: Calculate them ourselves
T = A./a .* sqrt(2*h0/g);

F = diag(-1./T);
F(1,3) = A(3)/A(1)/T(3);
F(2,4) = A(4)/A(2)/T(4);

G = zeros(4,2);
G(1,1) = gamma1*k1/A1;
G(2,2) = gamma2*k2/A2;
G(3,2) = (1-gamma2)*k2/A3;
G(4,1) = (1-gamma1)*k1/A4;

%% Is the linearized system controllable?
unco = length(A) - rank(ctrb(F, G));
if unco == 0; fprintf("Controllable\n"); end

%% Transfer function
s = tf('s');

c1 = T(1)*k1*kc/A1;
c2 = T(2)*k2*kc/A2;

H11 = gamma1*c1/(1+s*T(1));
H12 = (1-gamma2)*c1/(1+s*T(1))/(1+s*T(3));
H21 = (1-gamma1)*c2/(1+s*T(4))/(1+s*T(2));
H22 = gamma2*c2/(1+s*T(2));

H = [H11 H12 H21 H22];

%% Analyze rlocus with different sample times
figure
p1 = subplot(2, 2, 1);
p2 = subplot(2, 2, 2);
p3 = subplot(2, 2, 3);
p4 = subplot(2, 2, 4);
hold on
for i=-4:0.5:10
    Ts = 10^i;
    fprintf("Sample time %d\n", Ts);
    subplot(p1); hold on; rlocus(c2d(H11, Ts, 'zoh')); title H11;
    subplot(p2); hold on; rlocus(c2d(H12, Ts, 'zoh')); title H12;
    subplot(p3); hold on; rlocus(c2d(H21, Ts, 'zoh')); title H21;
    subplot(p4); hold on; rlocus(c2d(H22, Ts, 'zoh')); title H22;
end
hold off;